'''
Library Requirements
    selenium
    beautifulsoup4
    pandas
    pyautogui
    webdriver_manager
    PyYAML
    lxml
'''
import time, random, os, csv, platform
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import pyautogui

from urllib.request import urlopen
from webdriver_manager.chrome import ChromeDriverManager # Install manager?
import re
import yaml
from datetime import datetime, timedelta

# import chardet

log = logging.getLogger(__name__)
print("Installing chrome manager...")
# TODO ChromeDriverManager().install() downloads 8 MB file each time script is run. 
#           Can this be cached or optomised?
#   driver = webdriver.Chrome(ChromeDriverManager().install())
#driver = webdriver.Chrome()

def setupLogger():
    dt = datetime.strftime(datetime.now(), "%m_%d_%y %H_%M_%S ")

    if not os.path.isdir('./logs'):
        os.mkdir('./logs')

    # TODO need to check if there is a log dir available or not
    logging.basicConfig(filename=('./logs/' + str(dt) + 'applyJobs.log'), filemode='w',
                        format='%(asctime)s::%(name)s::%(levelname)s::%(message)s', datefmt='./logs/%d-%b-%y %H:%M:%S')
    log.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)
    c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%H:%M:%S')
    c_handler.setFormatter(c_format)
    log.addHandler(c_handler)


class EasyApplyBot:
    setupLogger()
    # MAX_SEARCH_TIME is 10 hours by default, feel free to modify it
    MAX_SEARCH_TIME = 10 * 60 * 60

    def __init__(self,
                 username,
                 password,
                 uploads={},
                 output_filename='output.csv',#Output.csv tracks all the JobIDs that have already been applied to
                 question_filename='questions.csv',
                 blacklist=[],
                 blackListTitles=[]):

        log.info("Welcome to Easy Apply Bot")
        dirpath = os.getcwd()
        log.info("current directory is : " + dirpath)

        self.uploads = uploads  # Holds path to file
        self.output_filename = output_filename
        past_ids = self.get_appliedIDs(output_filename)# [1:]
        self.appliedJobIDs = past_ids if past_ids != None else []
        self.question_filename = question_filename
        questions = self.get_questions(question_filename)
        self.questions = questions if questions != None else []
        self.options = self.browser_options()
        # self.browser = driver 
        self.browser = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.browser, 30)
        self.blacklist = blacklist
        self.blackListTitles = blackListTitles

        self.start_linkedin(username, password)

    def get_appliedIDs(self, output_filename):
        try:
            df = pd.read_csv(output_filename,
                             header=None,
                             names=['timestamp', 'jobID', 'job', 'company', 'attempted', 'result'],
                             lineterminator='\n',
                             encoding='utf-8')
            #df = df.drop_duplicates(subset='jobID', keep="first")
            # Why is timestamp used here?
            # If a job is applied to, leave it in the past you cant reapply
            # df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S")
            # df = df[df['timestamp'] > (datetime.now() - timedelta(days=2))]
            jobIDs = list(df.jobID)
            log.info(f"{len(jobIDs)} jobIDs found")
            return jobIDs
        except Exception as e:
            log.info(str(e) + "   jobIDs could not be loaded from CSV {}".format(output_filename))
            return None

    def get_questions(self, question_filename):
        # TODO Import and export questions encountered
        try:
            df = pd.read_csv(question_filename,
                            header=None,
                            names=['question', 'answer'],
                            lineterminator='\n',
                            encoding='utf-8')

            return df

        except Exception as e:
            log.info(str(e) + "    questions failed to load from CSV {0}".format(question_filename))
            return None

    def browser_options(self):
        options = Options()
        # options.add_argument("--headless")
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")

        

        # Disable webdriver flags or you will be easily detectable
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        return options

    def start_linkedin(self, username, password):
        log.info("Logging in.....Please wait :)  ")
        self.browser.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
        try:
            #Find element by the given ID in the webpage
            user_field = self.browser.find_element(By.ID, "username")
            pw_field = self.browser.find_element(By.ID, "password")
            login_button = self.browser.find_element(By.CSS_SELECTOR, ".btn__primary--large")
            user_field.send_keys(username)
            user_field.send_keys(Keys.TAB)
            time.sleep(2)
            pw_field.send_keys(password)
            time.sleep(2)
            login_button.click()
            time.sleep(3)
        except TimeoutException:
            log.info("TimeoutException! Username/password field or login button not found")

    def fill_data(self):
        self.browser.set_window_position(0, 0)
        self.browser.set_window_size(2000, 2000)
        '''
        self.browser.set_window_size(0, 0)
        self.browser.set_window_position(2000, 2000)
        '''

    def start_apply(self, positions, locations):
        start = time.time()
        self.fill_data()

        combos = []
        while len(combos) < len(positions) * len(locations):
            position = positions[random.randint(0, len(positions) - 1)]
            location = locations[random.randint(0, len(locations) - 1)]
            combo = (position, location)
            if combo not in combos:
                combos.append(combo)
                log.info(f"Applying to {position}: {location}")
                location = "&location=" + location
                # Primary Loop Function
                self.applications_loop(position, location)
            if len(combos) > 500:
                break

    # self.finish_apply() --> this does seem to cause more harm than good, since it closes the browser which we usually don't want, other conditions will stop the loop and just break out

    def applications_loop(self, position, location):

        count_application = 0
        count_job = 0
        jobs_per_page = 0
        start_time = time.time()

        log.info("Looking for jobs.. Please wait..")

        self.browser.set_window_position(0, 0)
        self.browser.maximize_window()
        self.browser, _ = self.next_jobs_page(position, location, jobs_per_page)
        log.info("Looking for jobs.. Please wait..")

        while time.time() - start_time < self.MAX_SEARCH_TIME:
            try:
                log.info(f"{(self.MAX_SEARCH_TIME - (time.time() - start_time)) // 60} minutes left in this search")

                # sleep to make sure everything loads, add random to make us look human.
                randoTime = random.uniform(3.5, 4.9)

                log.debug(f"Sleeping for {round(randoTime, 1)}")

                time.sleep(randoTime)
                self.load_page(sleep=1)

                # LinkedIn displays the search results in a scrollable <div> on the left side, we have to scroll to its bottom
                # This will be a single element
                scrollresults = self.browser.find_element(By.CLASS_NAME, "jobs-search-results-list")

                # Selenium only detects visible elements; if we scroll to the bottom too fast, only 8-9 results will be loaded into IDs list
                for i in range(300, 3000, 100):
                    self.browser.execute_script("arguments[0].scrollTo(0, {})".format(i), scrollresults)

                time.sleep(1)

                # get job ID (LinkedIn uses a predictable job iD format)
                links = self.browser.find_elements(By.XPATH, '//div[@data-job-id]')
        
                # log.debug(f' Count: {len(links)} Job Links: {links}')

                if len(links) == 0:
                    break 

                # get job ID of each job link
                # TODO Blacklist skip here
                IDs = []
                for link in links:
                    children = link.find_elements(By.XPATH, './/a[@data-control-id]')
                    # children = link.find_elements(By.ID, "data-job-id")
                    # log.debug(f'children: {children}')
                    for child in children:
                        if child.text not in self.blacklist:
                            temp = link.get_attribute("data-job-id")
                            jobID = temp.split(":")[-1]
                            IDs.append(int(jobID))
                IDs = set(IDs)

                # remove already applied jobs
                before = len(IDs)
                #jobIDs = [x for x in IDs if x not in self.appliedJobIDs]
                jobIDs = []
                for x in IDs:
                    if str(x) not in self.appliedJobIDs:
                        jobIDs.append(x)
                after = len(jobIDs)
                '''
                print(self.appliedJobIDs)
                print("Before {0}".format(before))
                print("After {0}".format(after))
                print(jobIDs)
                input("-------")
                '''

                # it assumed that 25 jobs are listed in the results window
                if len(jobIDs) == 0 and len(IDs) > 23:
                    jobs_per_page = jobs_per_page + 25
                    count_job = 0
                    self.avoid_lock()
                    self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                    location,
                                                                    jobs_per_page)
                # loop over IDs to apply
                for i, jobID in enumerate(jobIDs):
                    count_job += 1

                    self.get_job_page(jobID)
                    # Before we try apply  need check if it has been applied to

                    applicationCheck = self.check_if_applied()
                    if applicationCheck is False:
                        # get easy apply button
                        button = self.get_easy_apply_button()
                        # word filter to skip positions not wanted

                        if button is not False:
                            if any(word in self.browser.title for word in blackListTitles):
                                log.info('skipping this application, a blacklisted keyword was found in the job position')
                                string_easy = "* Contains blacklisted keyword"
                                result = False
                            else:
                                string_easy = "* has Easy Apply Button"
                                log.info("Clicking the EASY apply button")
                                button.click()
                                time.sleep(2)
                                result = self.send_resume()
                                count_application += 1
                                big_sleep = False  #
                        else:
                            log.info("The button does not exist.")
                            string_easy = "* Doesn't have Easy Apply Button"
                            result = False

                        position_number = str(count_job + jobs_per_page)
                        log.info(f"\nPosition {position_number}:\n {self.browser.title} \n {string_easy} \n")

                        self.write_to_file(button, jobID, self.browser.title, result)

                        if count_application != 0 and count_application % 20 == 0 and not big_sleep:
                            sleepTime = random.randint(500, 900)
                            log.info(f"""********count_application: {count_application}************\n\n
                                        Time for a nap - see you in:{int(sleepTime / 60)} min
                                    ****************************************\n\n""")
                            big_sleep = True
                            time.sleep(sleepTime)
                    else:
                        log.info(f"\nAlready applied to {self.browser.title} \n")
                    # sleep every 20 applications


                    # go to new page if all jobs are done
                    if count_job == len(jobIDs):
                        jobs_per_page = jobs_per_page + 25
                        count_job = 0
                        log.info("""****************************************\n\n
                        Going to next jobs page, YEAAAHHH!!
                        ****************************************\n\n""")
                        self.avoid_lock()
                        self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                        location,
                                                                        jobs_per_page)
            except Exception as e:
                log.debug(e)

    def write_to_file(self, button, jobID, browserTitle, result):
        def re_extract(text, pattern):
            target = re.search(pattern, text)
            if target:
                target = target.group(1)
            return target

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        attempted = False if button == False else True
        job = re_extract(browserTitle.split(' | ')[0], r"\(?\d?\)?\s?(\w.*)")
        company = re_extract(browserTitle.split(' | ')[1], r"(\w.*)")

        toWrite = [timestamp, jobID, job.replace(',', ' '), company.replace(',', ' '), attempted, result]
        with open(self.output_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(toWrite)

    def get_job_page(self, jobID):
        # job = 'https://www.linkedin.com/jobs/view/3841841542/'
        job = 'https://www.linkedin.com/jobs/view/' + str(jobID)
        self.browser.get(job)
        self.job_page = self.load_page(sleep=0.5)
        return self.job_page

    def check_if_applied(self):
        try:
            output = self.browser.find_elements(By.CLASS_NAME, 'post-apply-timeline__entity-time')
            # If output is empty
            if not output:
                applicationStatus = False
            else:
                applicationStatus = True
        except:
            applicationStatus = False
        return applicationStatus

    def get_easy_apply_button(self):
        try:
            # button = self.browser.find_elements(By.XPATH, '//button[contains(@class, "jobs-apply-button")]')
            button = self.browser.find_elements(By.XPATH, '//button[contains(@class, "jobs-apply-button")]/span[1]')
            # button = self.browser.find_elements(By.XPATH, '//button[contains(@class, "jobs-apply-button")]/span[contains(@class, "artdeco-button__text")]')
            EasyApplyButton = button[1]
        except:
            EasyApplyButton = False

        return EasyApplyButton

    def send_resume(self):
        # TODO O so much
        # Check for additional questions in the application form
        #   These questions need to be recorded in a CSV
        #   These questions need to be loaded with answers from a CSV
        #   
        def is_present(button_locator):
            present = len(self.browser.find_elements(button_locator[0],
                                                  button_locator[1])) > 0
            # log.debug(f' {present}')
            return present
        

        try:
            time.sleep(random.uniform(1.5, 2.5))
            next_locater = (By.CSS_SELECTOR,
                            "button[aria-label='Continue to next step']")
            review_locater = (By.CSS_SELECTOR,
                              "button[aria-label='Review your application']")
            submit_locater = (By.CSS_SELECTOR,
                              "button[aria-label='Submit application']")
            submit_application_locator = (By.CSS_SELECTOR,
                                          "button[aria-label='Submit application']")
            done_locator = (By.CLASS_NAME, 
                            "artdeco-button" )
            # error_locator = (By.CSS_SELECTOR,
            #                  "p[data-test-form-element-error-messages='true']")
            error_locator = (By.CLASS_NAME,
                             "artdeco-inline-feedback__message")
            # upload_locator = (By.CSS_SELECTOR, "input[name='file']")
            upload_locator = (By.CSS_SELECTOR,
                              "input[name='file']")
            # pattern to find the choose button
            choose_locator = (By.CSS_SELECTOR,
                              "button[aria-label='Choose Resume']")
            
            follow_locator = (By.CSS_SELECTOR, 
                              "label[for='follow-company-checkbox']")
            # Privacy Policy next_locater
            privacy_policy_locator = (By.XPATH, 
                                      "//*[text()='I Agree Terms & Conditions']")
            applied_locator = (By.CLASS_NAME, 'post-apply-timeline__entity-time')
            # Subsection Title locator
            title_locator = (By.XPATH, 
                             "//h3[@class='t-16 t-bold']")
            # Questions identifier

            # Required question locator
            required_locator = (By.CLASS_NAME, 
                                "fb-dash-form-element__label.fb-form-element-label__title--is-required")
            # Yes Radio button locator
            radio_locator_yes = (By.XPATH, 
                                 "//input[@data-test-text-selectable-option__input='Yes']")
            # No Radio button locator
            radio_locator_no = (By.XPATH, 
                                "//input[@data-test-text-selectable-option__input='No']")
            
            # Additional Button i need to add here

            submitted = False

            while True:
                if is_present(applied_locator):
                    submitted = True
                    break

                button = None
                # Resume & Upload Cover Letter if possible
                if is_present(choose_locator):
                    # button = self.wait.until(EC.element_to_be_clickable(privacy_policy_locator))
                    choose_button = self.browser.find_elements(choose_locator[0], choose_locator[1])
                    choose_button[0].click()
                    time.sleep(random.uniform(4.5, 6.5))

                # log.debug('Upload Locator Triggered??')
                # if is_present(upload_locator):
                #     log.info('NOTE UPLOAD BUTTON LOCATED')
                #     input_buttons = self.browser.find_elements(upload_locator[0],
                #                                                upload_locator[1])

                #     for input_button in input_buttons:
                #         # log.debug(f'input_button: {input_button}')
                #         parent = input_button.find_element(By.XPATH, "..")
                #         sibling = parent.find_element(By.XPATH, "preceding-sibling::*")
                #         grandparent = sibling.find_element(By.XPATH, "..")
                #         for key in self.uploads.keys():
                #             sibling_text = sibling.text
                #             gparent_text = grandparent.text
                #             # log.debug(f'key {key}')
                #             # log.debug(f'sibling_text {sibling_text}')
                #             # log.debug(f'gparent_text {gparent_text}')
                #             if key.lower() in sibling_text.lower() or key in gparent_text.lower():
                #                 input_button.send_keys(self.uploads[key])

                #     # input_button[0].send_keys(self.cover_letter_loctn)
                #     time.sleep(random.uniform(4.5, 6.5))

                # print(self.browser.find_elements(privacy_policy_locator))
                # Agree to T&Cs
                # log.debug('privacy_policy Locator Triggered??')
                if is_present(privacy_policy_locator):
                    button = self.wait.until(EC.element_to_be_clickable(privacy_policy_locator))
                    button.click()

                # Not sure how this code will work for multipule radio locator questions
                # TODO 
                # is_present check on additional questions
                # FIX title catch
                # Create generic function for question processing
                # try:
                #     section_title = self.browser.find_element(title_locator[0], title_locator[1]).text
                #     if section_title == "Additional" or section_title == "Additional Questions":
                #         questions = self.browser.find_elements(required_locator[0], required_locator[1])
                #         for question in questions:
                #             if question.text == "Will you now or in the future require sponsorship for employment visa status?":
                #                 radio_buttons = self.browser.find_elements(radio_locator_no[0], radio_locator_no[1])
                #                 radio_buttons[0].click()
                #             # if question.text == "Are you comfortable commuting to this job's location?":
                #             #     radio_buttons = self.browser.find_elements(radio_locator_yes[0], radio_locator_yes[1])
                #             #     radio_buttons[1].click()
                # except Exception as e:
                #     log.debug(f'Section Detection encountered an error...')
                #     print(e)

                '''
                count = 0
                total_questions = len(questions)
                count += 1

                required_elements_arr = self.browser.find_elements(required_locator[0], required_locator[1])
                for i, required_elem    ent in enumerate(required_elements_arr):
                    print("index: {0} ---- Text:  {1}".format(i, required_element.text))
                input("We at the additional Questions yo")
                for element in self.browser.find_elements(required_elements_locator):
                    input(element)
                '''

                # Click Next or submit button if possible
                button = None
                buttons = [next_locater, review_locater, follow_locator,
                           submit_locater, submit_application_locator, done_locator]
                for i, button_locator in enumerate(buttons):
                    
                    if is_present(button_locator):
                        # log.debug(f'Generic button locator trigger?? {button_locator}')
                        button = self.wait.until(EC.element_to_be_clickable(button_locator))

                    if is_present(error_locator):
                        # log.debug(f'error locator trigger?? ')
                        for element in self.browser.find_elements(error_locator[0],
                                                                  error_locator[1]):
                            text = element.text
                            if "Please enter a valid answer" in text:
                                log.info("Required question encountered, RIP...")
                                time.sleep(10)
                                button = None
                                break

                    if button:
                        button.click()
                        time.sleep(random.uniform(1.5, 2.5))
                        if i in (3, 4):
                            submitted = True
                        if i != 2:
                            break
                if button == None:
                    log.info("Could not complete submission")
                    break
                elif submitted:
                    log.info("Application Submitted")
                    break

            time.sleep(random.uniform(1.5, 2.5))


        except Exception as e:
            log.info(e)
            log.info("cannot apply to this job")
            raise (e)

        return submitted

    def load_page(self, sleep=1):
        scroll_page = 0
        while scroll_page < 5000:
            self.browser.execute_script("window.scrollTo(0," + str(scroll_page) + " );")
            scroll_page += 200
            time.sleep(sleep)

        if sleep != 1:
            self.browser.execute_script("window.scrollTo(0,0);")
            time.sleep(sleep * 3)

        page = BeautifulSoup(self.browser.page_source, "lxml")
        return page

    def avoid_lock(self):
        x, _ = pyautogui.position()
        pyautogui.moveTo(x + 200, pyautogui.position().y, duration=1.0)
        pyautogui.moveTo(x, pyautogui.position().y, duration=0.5)
        pyautogui.keyDown('ctrl')
        pyautogui.press('esc')
        pyautogui.keyUp('ctrl')
        time.sleep(0.5)
        pyautogui.press('esc')

    def next_jobs_page(self, position, location, jobs_per_page):
        self.browser.get(
            "https://www.linkedin.com/jobs/search/?f_LF=f_AL&keywords=" +
            position + location + "&start=" + str(jobs_per_page))
            #  + "&f_E=2%2C3"
            # &f_E=2%2C3%2C4 - Entry, Assosiate, Mid
            # &f_E=2%2C3 - Entry, Assosiate

        self.avoid_lock()
        log.info("Lock avoided.")
        self.load_page()
        return (self.browser, jobs_per_page)

    def finish_apply(self):
        self.browser.close()

    # # Auto Application review script
    # def review_applications(self):
    #     file_name = "output.csv"
    #     with open(file_name, 'rb') as f:
    #         result = chardet.detect(f.read())
    #         encoding = result['encoding']

    #     # for chunk in pd.read_csv(file_name, sep=',', header=0, encoding=encoding):
    #     #     print(chunk)
    #     #     input("----")
    #     applicationData = pd.read_csv("output.csv", sep=',', header=0, encoding=encoding)
    #     # applicationData = pd.read_csv("output copy.csv", sep=',', header=0)

    #     print("Cleaning duplicates...")
    #     applicationData = applicationData.drop_duplicates(subset="jobID", keep='first')
    #     TotaltoReview = len(applicationData.drop(applicationData[applicationData['result'] != False].index))

    #     print("-----------------------------------------------")
    #     print("***********************************************")
    #     print('Total Entries: {0}'.format(len(applicationData.index)))
    #     print('Entries to Review: {0}'.format(TotaltoReview))
    #     print("***********************************************")
    #     print("-----------------------------------------------")

    #     url = "https://www.linkedin.com/jobs/view/"

    #     count = 0
    #     for dfindex, row in applicationData.iterrows():
    #         if row['result'] is False:
    #             ID = str(row["jobID"])
                
    #             wb.open(url + ID)

    #             # Column then index then cell
    #             applicationData.at[dfindex, 'jobID'] = ID
    #             applicationData.at[dfindex, 'attempted'] = True
    #             applicationData.at[dfindex, 'result'] = True

    #             # applicationData.set_value(dfindex, 'result', True)

    #             count += 1
    #             if count % 10 == 0:
    #                 applicationData.to_csv('output.csv', sep=',', index=False)
    #                 print("-----------------------------------------------")
    #                 print("--------------- Saving Progress ---------------")
    #                 print("-----------------------------------------------")

    #             print('Position: {0}'.format(row["job"]))
    #             print('Company: {0}'.format(row["company"]))
    #             print("")
    #             print('Total Applications to Review: {0}'.format(TotaltoReview))
    #             print('Reviewed: {0}'.format(count))
    #             print("-----------------------------------------------")
    #             print("----------------- Press Enter -----------------")
    #             input("-----------------------------------------------")
    #             print("")
                
    #     applicationData.to_csv('output.csv', sep=',', index=False)

if __name__ == '__main__':

    with open("config.yaml", 'r') as stream:
        try:
            parameters = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise exc

    assert len(parameters['positions']) > 0
    assert len(parameters['locations']) > 0
    assert parameters['username'] is not None
    assert parameters['password'] is not None

    if 'uploads' in parameters.keys() and type(parameters['uploads']) == list:
        raise Exception("uploads read from the config file appear to be in list format" +
                        " while should be dict. Try removing '-' from line containing" +
                        " output_filename & path")

    log.info({k: parameters[k] for k in parameters.keys() if k not in ['username', 'password']})

    filename = [f for f in parameters.get('filename', ['output.csv']) if f != None]
    filename = filename[0] if len(filename) > 0 else 'output.csv'
    blacklist = parameters.get('blacklist', [])
    blackListTitles = parameters.get('blackListTitles', [])

    uploads = {} if parameters.get('uploads', {}) == None else parameters.get('uploads', {})
    for key in uploads.keys():
        assert uploads[key] != None

    bot = EasyApplyBot(parameters['username'],
                       parameters['password'],
                       uploads=uploads,
                       output_filename=filename,
                       blacklist=blacklist,
                       blackListTitles=blackListTitles
                       )

    locations = [l for l in parameters['locations'] if l != None]
    positions = [p for p in parameters['positions'] if p != None]
    bot.start_apply(positions, locations)

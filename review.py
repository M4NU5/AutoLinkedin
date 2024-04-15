import pandas as pd
import webbrowser as wb
import chardet

# CSV File format
# timestamp, jobID, job, company, attempted, result


def ReviewApplications():
    file_name = "output.csv"
    with open(file_name, 'rb') as f:
        result = chardet.detect(f.read())
        encoding = result['encoding']

    # for chunk in pd.read_csv(file_name, sep=',', header=0, encoding=encoding):
    #     print(chunk)
    #     input("----")
    applicationData = pd.read_csv("output.csv", sep=',', header=0, encoding=encoding)
    # applicationData = pd.read_csv("output copy.csv", sep=',', header=0)

    print("Cleaning duplicates...")

    applicationData = applicationData.drop_duplicates(subset="jobID", keep='first')
    TotaltoReview = len(applicationData.drop(applicationData[applicationData['result'] != False].index))

    print("-----------------------------------------------")
    print("***********************************************")
    print('Total Entries: {0}'.format(len(applicationData.index)))
    print('Entries to Review: {0}'.format(TotaltoReview))
    print("***********************************************")
    print("-----------------------------------------------")

    url = "https://www.linkedin.com/jobs/view/"

    count = 0
    for dfindex, row in applicationData.iterrows():
        if row['result'] is False:
            ID = str(row["jobID"])

            # Column then index then cell
            applicationData.at[dfindex, 'jobID'] = ID
            applicationData.at[dfindex, 'attempted'] = True
            applicationData.at[dfindex, 'result'] = True

            # applicationData.set_value(dfindex, 'result', True)

            count += 1
            if count % 10 == 0:
                applicationData.to_csv('output.csv', sep=',', index=False)
                print("-----------------------------------------------")
                print("--------------- Saving Progress ---------------")
                print("-----------------------------------------------")

            print('Position: {0}'.format(row["job"]))
            print('Company: {0}'.format(row["company"]))
            print("")
            print('Total Applications to Review: {0}'.format(TotaltoReview))
            print('Reviewed: {0}'.format(count))
            print("-----------------------------------------------")
            print("------------- Press Enter or Skip -------------")
            user_input = input("-----------------------------------------------")
            if user_input == "":
                wb.open(url + ID)
            print("")



    applicationData.to_csv('output.csv', sep=',', index=False)


if __name__ == '__main__':
    ReviewApplications()

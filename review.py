import pandas as pd
import webbrowser as wb

# CSV File format
# timestamp, jobID, job, company, attempted, result


def ReviewApplications():
    for chunk in pd.read_csv("output.csv", sep=',', header=0):
        print(chunk)
        input("----")
    applicationData = pd.read_csv("output.csv", sep=',', header=0)
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
            wb.open(url + ID)

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
            print("----------------- Press Enter -----------------")
            input("-----------------------------------------------")
            print("")



    applicationData.to_csv('output.csv', sep=',', index=False)


if __name__ == '__main__':
    ReviewApplications()

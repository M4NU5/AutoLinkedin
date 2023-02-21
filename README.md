# Linkedin EasyApply Bot
Automate the application process on LinkedIn

Medium Write-up: https://medium.com/xplor8/how-to-apply-for-1-000-jobs-while-you-are-sleeping-da27edc3b703

Video: https://www.youtube.com/watch?v=4R4E304fEAs

## Setup 

The run the bot install requirements. Advised you generate a venv for this.
```bash
pip3 install -r requirements.txt
```

Enter your username, password, and search settings into the `config.yaml` file

```yaml
username: # Insert your username here
password: # Insert your password here

positions:
- # positions you want to search for
- # Another position you want to search for
- # A third position you want to search for

locations:
- # Location you want to search for
- # A second location you want to search in 

uploads:
 Resume: # PATH TO Resume 
 Cover Letter: # PATH TO cover letter
 Photo: # PATH TO photo
# Note file_key:file_paths contained inside the uploads section should be writted without a dash ('-') 

output_filename:
- # PATH TO OUTPUT FILE (default output.csv)

blacklist:
- # Company names you want to ignore
```
__NOTE: AFTER EDITING SAVE FILE, DO NOT COMMIT FILE__

### Uploads

There is no limit to the number of files you can list in the uploads section. 
The program takes the titles from the input boxes and tries to match them with 
list in the config file.

## Execute

To execute the bot run the following in your terminal
```bash
python3 easyapplybot.py
```



## Review.py
A review script i wrote to iterate through the generated 'output.csv' file.
Execution:
```bash
python3 review.py
```

### Script guide
It will display a text element of the failed job application.
IF job title is of interest press 'Enter'
    This will open the job page
If the job title is NOT of interest press a random key then 'Enter' 
    This will skip the job
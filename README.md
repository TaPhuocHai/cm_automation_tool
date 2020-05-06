# cm_automation_tool

## How To Install
1) Python
Ensure you have Python version 3.6 or later. Kindly visit https://www.python.org/ and download Python version 3 on your system.

2) Clone or simply download the code

3) Install virtual environment package (Highly recommend but not 100% necessary)

> python -m pip install --user virtualenv
Then create an isolated virtual enviroment
> python -m virtualenv ematic_env

4) Activate the virtual enviroment (You can skip this if you don't do step 3)
> source ematic_env/bin/activate

5) Install dependencies for our program
> pip install -r requirements.txt

## How to Use

#### Suppression/Unsuppression tool

1. There are 2 folders: suppression_list and unsuppression_list. Place the data in csv or excel format (xlsx, xls). 

2. Then, we need to provide credentials of the Campaign Monitor account. Kindly open the file .env_example, copy and paste in to a new file ".env" at the same root directory. Then please change the information accordingly depending on your intention (suppressing or unsuppressing e-mail addresses).


3. Run the command  if you want to suppressing email addresses
> python cm_automation_tool_suppresing.py

Or if you want to unsuppressing email addressed

> python cm_automation_tool_unsuppresing.py

#### Preclean tool

First, we need to provide credentials. Kindly open the file .env_example, copy and paste in to a new file ".env" at the same root directory. Then please change the information accordingly.

You also need to have 2 folder: input and output.

In the input folder, place the data in csv or excel format (xlsx, xls). Then open the file cm_automation.py, change the constant NEW_DATA to the name of the new data file.

Open our VPN connection and run 

\> python cm_automation.py
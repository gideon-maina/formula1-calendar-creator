# formula1-calendar-creator
Crawl the formula 1 calendar and create an ics calendar file that you can then import into google calendar

# How to run
Ensure you have

1. Python
2. Virtualenv
3. Scrapy installed in the env
4. Clone this repo
5. Navigate to the root directory and run the command `$ scrapy crawl schedule -a calendar_name="The 2022 FIA Formula One World Championship" -a calendar_description="Description"`
6. By default the output .ics file will be in the same directory named with the year prepended  e.g  `2022-Formula-1-Calendar.ics` for 2022
7. You can specify the file to save by adding an arg `-a output_file=<file_path>`

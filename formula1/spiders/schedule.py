from datetime import datetime, timezone
from uuid import uuid4

from scrapy import shell
import scrapy

BASE_URL = "https://www.formula1.com/"
ICAL = """BEGIN:VCALENDAR
PRODID:-//Google Inc//Google Calendar 70.9054//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:{calendar_name}
X-WR-TIMEZONE:UTC
X-WR-CALDESC:{calendar_description}
"""


class ScheduleSpider(scrapy.Spider):
    name = "schedule"
    total_grand_prix = 0
    crawled_grand_prix = 0

    def __init__(
        self,
        calendar_name: str = f"Formula 1 Calendar {datetime.now().strftime('%Y')}",
        calendar_description: str = "Formula 1 Calendar",
        output_file: str = f"{datetime.now().strftime('%Y')}-Formula-1-Calendar.ics",
        **kwargs,
    ):
        self.ical = ICAL.format(
            calendar_name=calendar_name, calendar_description=calendar_description
        )
        self.output_file = output_file
        super().__init__(**kwargs)

    def start_requests(self):
        urls = [
            f"https://www.formula1.com/en/racing/{datetime.now().strftime('%Y')}.html"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        links = response.xpath(
            '//div[contains(@class, "row") and contains(@class, "completed-events")]/div/a'
        )
        self.total_grand_prix = len(links)
        for l in links:
            link = l.attrib["href"]
            yield scrapy.Request(url=BASE_URL + link, callback=self.event_callback)

    def event_callback(self, response):
        title = response.xpath('//h2[@class="f1--s"]/text()').get().title()
        print(f"Grand Prix {title}")
        desc = response.xpath(
            '//div[contains(@class, "f1-race-hub--body-text") and contains(@class, "f1-race-hub--content") and contains(@class, "container")]/p/text()'
        )
        description = ""
        for d in desc:
            description += d.get()
        location = response.xpath(
            '//p[contains(@class, "f1-uppercase") and contains(@class, "misc--tag") and contains(@class, "no-margin")]/text()'
        ).get()
        events = response.xpath('//div[@class="f1-race-hub--timetable-listings"]/div')
        ical_event = []
        for e in events:
            name = " ".join(
                n.strip().capitalize()
                for n in e.attrib["class"]
                .replace("js-", "")
                .replace("row", "")
                .split("-")
            )
            tz = e.attrib["data-gmt-offset"].replace(":", "")
            start_time = e.attrib["data-start-time"] + tz
            end_time = e.attrib["data-end-time"] + tz
            st_ts = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z")
            end_ts = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S%z")
            print(f"Event {name}, {st_ts.astimezone(timezone.utc)}, {end_time}")
            ical_event.append("BEGIN:VEVENT")
            ical_event.append(f"UID:{uuid4()}")
            ical_event.append(
                f"DTSTART:{st_ts.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
            )
            ical_event.append(
                f"DTEND:{end_ts.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
            )
            ical_event.append(
                f"CREATED:{datetime.now().astimezone(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
            )
            ical_event.append(f"DESCRIPTION:{description}")
            ical_event.append(f"LOCATION:{location}")
            ical_event.append("SEQUENCE:0")
            ical_event.append("STATUS:CONFIRMED")
            ical_event.append(f"SUMMARY:({name}) - {title}")
            ical_event.append("TRANSP:OPAQUE")
            ical_event.append("END:VEVENT\n")
            self.ical += "\n".join(ical_event)
            ical_event = []
        print("*" * 80)
        self.crawled_grand_prix += 1
        if self.crawled_grand_prix == self.total_grand_prix:
            self.write_to_file()

    def write_to_file(self):
        with open(self.output_file, "w") as fh:
            fh.write(self.ical)
            fh.write("END:VCALENDAR")
            print(f"Written calendar to file {self.output_file}")

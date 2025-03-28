#!/usr/bin/env python3

import gi
import sys
import re
import os
import time
from datetime import datetime, timedelta

gi.require_version("Gtk", "3.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk, GLib, Pango, Gdk, Gio


def parse_command_line_args():
    time_str = sys.argv[1]
    if re.match(r"^\d{2}:\d{2}$", time_str):
        hour, minute = map(int, time_str.split(":"))
        today = datetime.now()
        end_time = today.replace(hour=hour, minute=minute, second=0)
        if end_time <= today:
            end_time += timedelta(days=1)
    else:
        end_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    return end_time


def wait_until_next_second():
    now = time.time()
    next_second = int(now) + 1
    sleep_time = next_second - now
    print(
        "Syncing... waiting {0:.2f} seconds until the next second in time... ".format(
            sleep_time
        ),
        end="",
    )
    time.sleep(sleep_time)
    print("Launching timer.")


class ClockWindow(Gtk.Window):
    def __init__(self, end_time):
        super().__init__(title="Timer ending at {}".format(end_time.strftime("%H:%M")))

        self.end_time = end_time

        # Load CSS from a string (or file)
        self.css_provider = Gtk.CssProvider()
        self.set_style(200)

        # Create labels for the clocks
        self.top_clock_label = Gtk.Label()
        self.top_clock_label.set_justify(Gtk.Justification.CENTER)
        self.top_clock_label.get_style_context().add_provider(
            self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.top_clock_label.get_style_context().add_class("white")
        self.bottom_clock_label = Gtk.Label()
        self.bottom_clock_label.set_justify(Gtk.Justification.CENTER)
        self.bottom_clock_label.get_style_context().add_provider(
            self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.bottom_clock_label.get_style_context().add_class("white")

        # Create a separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.get_style_context().add_provider(
            self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Set initial time
        current_time, remaining_time = self.get_times()
        self.top_clock_label.set_text(current_time)
        self.bottom_clock_label.set_text(remaining_time)

        # Create a vertical box layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.pack_start(self.top_clock_label, True, True, 0)
        vbox.pack_start(separator, False, False, 0)  # Add the separator
        vbox.pack_start(self.bottom_clock_label, True, True, 0)

        self.add(vbox)
        self.set_default_size(1000, 400)
        self.get_style_context().add_provider(
            self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.timeout_id = GLib.timeout_add(1000, self.update_clock)

        self.connect("size-allocate", self.on_size_allocate)
    
    def on_size_allocate(self, widget, allocation):
        width = allocation.width
        height = allocation.height
        font_size = min(width, height) * 0.4
        self.set_style(font_size)
    
    def set_style(self, font_size):
        css = f"""
            label {{
                font-family: "alarm clock";
                font-size: {font_size}px;
            }}

            .white {{
                color: white;
            }}

            .red {{
                color: red;
            }}

            separator {{
                background-color: white;
            }}

            window {{
                background-color: black;
            }}
        """
        self.css_provider.load_from_data(css.encode())


    def update_clock(self):
        current_time, remaining_time = self.get_times()
        self.top_clock_label.set_text(current_time)
        self.bottom_clock_label.set_text(remaining_time)
        return True

    def get_times(self):
        now = datetime.now()
        now = now.replace(microsecond=0)
        current_time = now.strftime("%H:%M:%S")
        time_left = self.end_time - now
        # print("{} - {}".format(now, time_left))
        if time_left.total_seconds() <= 0:
            remaining_time = "00:00:00"
            self.bottom_clock_label.get_style_context().add_class("red")
        else:
            total_hours = time_left.total_seconds() / 3600
            hours = int(total_hours)
            minutes = int((total_hours - hours) * 60)
            seconds = int(((total_hours - hours) * 60 - minutes) * 60)
            if seconds >= 60:
                seconds = 0
            remaining_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return current_time, remaining_time

    def destroy(self):
        GLib.source_remove(self.timeout_id)
        super().destroy()


if __name__ == "__main__":
    try:
        target_time = parse_command_line_args()
    except IndexError:
        print("Missing argument. Please specify time.")
        sys.exit(1)
    except ValueError:
        print(
            "Invalid time format. Please use YYYY-MM-DD HH:MM:SS (e.g., 2024-12-31 23:59:59) or HH:MM (e.g., 23:59)."
        )
        sys.exit(1)
    wait_until_next_second()
    win = ClockWindow(target_time)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

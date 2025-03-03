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
    if len(sys.argv) > 1:
        time_str = sys.argv[1]

        if re.match(r"^\d{2}:\d{2}$", time_str):
            try:
                hour, minute = map(int, time_str.split(":"))
                # Create a datetime object for today at the specified time
                today = datetime.now()
                end_time = today.replace(hour=hour, minute=minute, second=0)
                # Ensure the end time is in the future
                if end_time <= today:
                    end_time += timedelta(
                        days=1
                    )  # Set it for tomorrow if it's already past today
            except ValueError:
                print("Invalid time format. Please use HH:MM (e.g., 23:59).")
                sys.exit(1)
        else:
            try:
                # Attempt to parse the provided argument as a datetime string
                end_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(
                    "Invalid time format. Please use YYYY-MM-DD HH:MM:SS (e.g., 2024-12-31 23:59:59) or HH:MM (e.g., 23:59)."
                )
                sys.exit(1)
        return end_time
    else:
        print(
            'Please enter a date/time. Supported formats: "HH:MM", "YYYY-MM-DD HH:MM:SS"'
        )
        sys.exit(1)


def wait_until_next_second():
    # Wait until the following second
    now = time.time()
    next_second = int(now) + 1
    sleep_time = next_second - now
    print(
        "Waiting {} seconds until the next second in time... ".format(sleep_time),
        end="",
    )
    time.sleep(sleep_time)
    print("Launching timer.")


class ClockWindow(Gtk.Window):
    def __init__(self, end_time):
        super().__init__(title="Timer ending at {}".format(end_time.strftime("%H:%M")))

        self.end_time = end_time

        # Load UI from glade file
        builder = Gtk.Builder()
        try:
            builder.add_from_file("timer.glade")
        except Exception as ex:
            print(f"Error loading Glade file: {ex}")
            exit(1)
        self.separator = builder.get_object("separator")
        self.top_clock_label = builder.get_object("top_clock_label")
        self.bottom_clock_label = builder.get_object("bottom_clock_label")

        css_provider = Gtk.CssProvider()
        css_provider.load_from_file(
            Gio.File.new_for_path(
                os.path.dirname(os.path.realpath(__file__)) + "/style.css"
            )
        )
        self.separator.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.top_clock_label.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.bottom_clock_label.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Set initial time
        current_time, remaining_time = self.get_times()
        self.top_clock_label.set_text(current_time)
        self.bottom_clock_label.set_text(remaining_time)

        # Schedule the clock update using GLib.timeout_add
        self.timeout_id = GLib.timeout_add(1000, self.update_clock)

    def update_clock(self):
        current_time, remaining_time = self.get_times()
        self.top_clock_label.set_text(current_time)
        self.bottom_clock_label.set_text(remaining_time)
        return True

    def get_times(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        time_left = self.end_time - now
        if time_left.total_seconds() <= 0:
            remaining_time = "00:00:00"
            self.bottom_clock_label.get_style_context().add_class("red")
        else:
            total_hours = time_left.total_seconds() / 3600
            hours = int(total_hours)
            minutes = int((total_hours - hours) * 60)
            seconds = int(((total_hours - hours) * 60 - minutes) * 60) + 1
            if seconds >= 60:
                seconds = 0
            remaining_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return current_time, remaining_time

    def destroy(self):
        # Cancel the timeout when the window is closed
        GLib.source_remove(self.timeout_id)
        super().destroy()


if __name__ == "__main__":
    wait_until_next_second()
    win = ClockWindow(parse_command_line_args())
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

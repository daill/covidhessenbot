#  Copyright 2019 Christian Kramer
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
#   (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge,
#   publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do
#   so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
#  LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
#  EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from html.parser import HTMLParser


class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.first_row = None
        self.row_count = -1
        self.p_tag = False
        self.title = []
        self.table = []

    def reset_results(self):
        self.title.clear()
        self.table.clear()
        self.in_table = False
        self.first_row = None
        self.row_count = -1
        self.p_tag = False

    def get_result(self):
        return self.title, self.table

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.in_table = True
        if tag == "tr":
            if self.first_row is None:
                self.first_row = True
            else:
                self.first_row = False
                self.row_count += 1
                self.table.insert(self.row_count, [])
        if tag == "p":
            self.p_tag = True

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        if tag == "p":
            self.p_tag = False

    def handle_data(self, data):
        if self.in_table and self.first_row:
            data = data.strip()
            if data:
                self.title.append(data)
        if self.in_table and not self.first_row:
            data = data.strip()
            if self.p_tag:
                self.table[self.row_count].append(data)
import requests  # still needed for any fallbacks
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.relativelayout import RelativeLayout
from kivy.metrics import dp
from kivy.clock import Clock

try:
    from libgen_api_enhanced import LibgenSearch, SearchType
except ImportError:
    print("Please install libgen-api-enhanced: pip install libgen-api-enhanced")

# ────────────────────────────────────────────────
#                KIVY UI
# ────────────────────────────────────────────────

class SearchUI(RelativeLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.container = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        self.add_widget(self.container)

        # Mirror selector (enhanced lib supports mirrors like .li, .bz, .gs)
        mirror_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        mirror_layout.add_widget(Label(text="Mirror:", size_hint_x=0.3))
        self.mirror_spinner = Spinner(
            text="li",
            values=["li", "bz", "gs"],
            size_hint_x=0.7
        )
        mirror_layout.add_widget(self.mirror_spinner)
        self.container.add_widget(mirror_layout)

        # Inputs
        self.isbn_input = TextInput(hint_text="ISBN", multiline=False, size_hint_y=None, height=dp(44))
        self.title_input = TextInput(hint_text="Title", multiline=False, size_hint_y=None, height=dp(44))
        self.author_input = TextInput(hint_text="Author", multiline=False, size_hint_y=None, height=dp(44))

        self.container.add_widget(self.isbn_input)
        self.container.add_widget(self.title_input)
        self.container.add_widget(self.author_input)

        # Format filter
        format_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        format_layout.add_widget(Label(text="Format:", size_hint_x=0.3))
        self.format_spinner = Spinner(
            text="Any",
            values=["Any", "epub", "pdf", "mobi", "azw", "azw3", "fb2", "txt", "rtf", "djvu"],
            size_hint_x=0.7
        )
        format_layout.add_widget(self.format_spinner)
        self.container.add_widget(format_layout)

        # Search button
        btn = Button(text="Search LibGen", size_hint_y=None, height=dp(56), background_color=(0.1, 0.5, 0.9, 1))
        btn.bind(on_release=self.start_search)
        self.container.add_widget(btn)

        # Status label
        self.status = Label(text="", size_hint_y=None, height=dp(32), color=(0.9, 0.9, 0.4, 1))
        self.container.add_widget(self.status)

        # Scroll results
        self.scroll = ScrollView(size_hint=(1, 1))
        self.results_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.results_layout.bind(minimum_height=self.results_layout.setter("height"))
        self.scroll.add_widget(self.results_layout)
        self.container.add_widget(self.scroll)

    def on_size(self, *args):
        w, h = self.size
        target_h = w * 9 / 16
        if target_h > h:
            target_w = h * 16 / 9
            self.container.size = (target_w, h)
            self.container.pos = ((w - target_w) / 2, 0)
        else:
            self.container.size = (w, target_h)
            self.container.pos = (0, (h - target_h) / 2)

    def start_search(self, *args):
        self.results_layout.clear_widgets()
        self.status.text = "Searching..."

        mirror = self.mirror_spinner.text
        isbn = self.isbn_input.text.strip()
        title = self.title_input.text.strip()
        author = self.author_input.text.strip()
        ext = self.format_spinner.text.strip().lower()
        ext_filter = {"extension": ext} if ext != "any" else {}

        Clock.schedule_once(lambda dt: self.do_search(mirror, isbn, title, author, ext_filter), 0.1)

    def do_search(self, mirror, isbn, title, author, ext_filter):
        try:
            s = LibgenSearch(mirror=mirror)
            
            if isbn:
                # For ISBN, use search_default or title with isbn filter
                results = s.search_default(isbn)
            elif title and author:
                # Combined
                results = s.search_title_filtered(f"{title} {author}", ext_filter, exact_match=False)
            elif title:
                results = s.search_title_filtered(title, ext_filter, exact_match=False)
            elif author:
                results = s.search_author_filtered(author, ext_filter, exact_match=False)
            else:
                self.status.text = "Enter search terms"
                return

            shown = 0
            for book in results:
                card = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(160),
                                 padding=dp(12), spacing=dp(6))
                
                lbl_title = Label(text=book.title[:100], bold=True, halign="left")
                card.add_widget(lbl_title)
                
                lbl_author = Label(text=f"By {book.author}", color=(0.3, 0.3, 0.8, 1), halign="left")
                card.add_widget(lbl_author)
                
                info = f"Year: {book.year} • {book.extension.upper()} • {book.size}"
                lbl_info = Label(text=info, color=(0.5, 0.5, 0.5, 1), font_size=dp(13), halign="left")
                card.add_widget(lbl_info)
                
                dl_btn = Button(text="Open Download Page", size_hint_y=None, height=dp(42))
                dl_url = book.mirrors[0]  # first mirror, or resolve book.resolve_direct_download_link()
                dl_btn.bind(on_release=lambda _, u=dl_url: self.open_browser(u))
                card.add_widget(dl_btn)
                
                self.results_layout.add_widget(card)
                shown += 1
                if shown >= 10:
                    break

            self.status.text = f"Found {shown} results" if shown > 0 else "No results - try different mirror/terms"
        except Exception as e:
            self.status.text = f"Error: {str(e)}"

    def open_browser(self, url):
        import webbrowser
        webbrowser.open(url)


class LibGenApp(App):
    def build(self):
        return SearchUI()


if __name__ == "__main__":
    LibGenApp().run()

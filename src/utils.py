
class StreamlitStdoutRedirector:
    def __init__(self, placeholder, max_chars: int = 8000):
        self.placeholder = placeholder
        self.output_str = ""
        self.max_chars = max_chars

    def reset(self):
        self.output_str = ""
        self.placeholder.empty()

    def write(self, text):
        if not text:
            return
        self.output_str += str(text)
        if len(self.output_str) > self.max_chars:
            self.output_str = self.output_str[-self.max_chars:]
        self.placeholder.code(self.output_str, language="text")

    # Add this exact method to satisfy sys.stdout
    def flush(self):
        pass
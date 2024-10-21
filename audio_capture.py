def stop_stream(self):
    if self.stream and self.stream.is_active():
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None

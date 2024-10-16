from common_logging import setup_logging

class ResponseProcessor:
    def __init__(self, config):
        self.full_transcript = ""
        self.logger = setup_logging('response_processor')
        self.question_starters = config.question_starters

    def process_transcript_delta(self, delta):
        self.full_transcript += delta
        self.logger.debug(f"Processed transcript delta: {delta}")
        return delta

    def is_question(self, text):
        if not text:
            return False
        text = text.lower().strip()
        is_question = (text.split()[0] in self.question_starters or text.endswith('?'))
        self.logger.debug(f"Is question: {is_question} for text: {text}")
        return is_question

    def get_full_transcript(self):
        return self.full_transcript

    def clear_transcript(self):
        self.full_transcript = ""
        self.logger.debug("Transcript cleared")

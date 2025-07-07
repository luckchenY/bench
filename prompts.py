# 所有 prompt 字符串将在此集中管理 

QA_PROMPT = """
1. You are a professional expert in analyzing Q&A sessions from scientific research videos. Please analyze the following audio and specifically extract the Q&A session that occurs after the main presentation.
Look for the following keywords or phrases, which usually indicate the start of the Q&A session:
"Does anyone have any questions?"
"Are there any questions?"
"Now we enter the Q&A session"
"Please ask questions"
"If you have questions, you can raise your hand"
"Let's start the Q&A"
"Next is the question time"
2. For each questioner, if the same person asks multiple follow-up questions on the same topic, and the same respondent answers, please combine all their consecutive exchanges into a single Q&A block. Each Q&A block should correspond to one questioner and one respondent, and should include all the follow-up questions and answers between them on the same topic. Do not mix questions from different people into the same block.
Only extract the live Q&A session, do not include the main presentation content.
Maintain the original order of the Q&A.
If a question is not academically meaningful, do not include it in your output.
Please convert colloquial expressions in the audio into written language, ensuring the generated content is fluent and clearly expressed.
Return the formatted Q&A content in the following format, and do not add any other explanations:
Q&A
question: [A complete question block, summarizing all consecutive questions from the same questioner on the same topic]
answer: [Corresponding answer block, summarizing all consecutive answers from the same respondent to that questioner on the same topic]
Q&A
question: [Next question block from another questioner]
answer: [Next answer block]
...
"""

Transcript_PROMPT = """
Please transcribe the recording into text and ensure the fluency of the dialogue text. 
If necessary, you may need to use the ability of a large language model to make some corrections to the text. 
The output text needs to conform to the punctuation and segmentation of normal speech.
"""
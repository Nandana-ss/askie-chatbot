import time
import openai
import os
import json
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

def send_email(to: str, subject: str, body: str):
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to, msg.as_string())
        server.quit()
        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Email failed to send: {e}")

def send_email_tool():
    return {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    }

def create_agent(context_text):
    with open("context.txt", "w", encoding="utf-8") as f:
        f.write(context_text)
    with open("context.txt", "rb") as f:
        uploaded_file = client.files.create(file=f, purpose="assistants")

    assistant = client.beta.assistants.create(
        name="Smart Chatbot",
        instructions=(
            "You are a helpful assistant. You can respond to general messages and trigger tools like sending emails if asked. "
            "But when asked about something specific, answer strictly based on the uploaded file."
        ),
        model="gpt-4o",
        tools=[send_email_tool()]
    )

    thread = client.beta.threads.create()

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=context_text
    )

    return {"assistant_id": assistant.id, "thread_id": thread.id}

def chat_with_agent(thread_id, message, user_email, assistant_id):
    try:
        runs = client.beta.threads.runs.list(thread_id=thread_id, limit=1)
        if runs.data and runs.data[0].status not in ["completed", "failed", "cancelled"]:
            return "⚠️ A previous request is still processing. Please wait a moment and try again."
    except Exception as e:
        return f"⚠️ Error checking active run: {e}"

    try:
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
    except openai.BadRequestError as e:
        return f"❌ Error adding message: {e}"

    try:
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
    except openai.BadRequestError as e:
        return f"❌ Error starting run: {e}"

    try:
        run_status = wait_for_run_completion(thread_id, run.id)
    except TimeoutError:
        return "⚠️ The assistant took too long to respond. Try again later."

    email_args = None

    if run_status.status == "requires_action":
        tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
        for call in tool_calls:
            if call.function.name == "send_email":
                args = json.loads(call.function.arguments)
                email_args = args

                client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=[
                        {
                            "tool_call_id": call.id,
                            "output": "Email sent successfully."
                        }
                    ]
                )

                run_status = wait_for_run_completion(thread_id, run.id)

    if run_status.status in ["completed", "requires_action"]:
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                if msg.content:
                    for part in msg.content:
                        if part.type == "text":
                            reply = part.text.value
                            if email_args:
                                send_email(email_args["to"], email_args["subject"], email_args["body"])
                                return f"📧 The email has been sent successfully to {email_args['to']} with the subject '{email_args['subject']}' and the body '{email_args['body']}'.\n\n🤖 {reply}"
                            return reply

    return "⚠️ No valid response from the assistant."

def wait_for_run_completion(thread_id, run_id, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run_status.status in ["completed", "requires_action", "failed", "cancelled"]:
            return run_status
        time.sleep(1)
    raise TimeoutError("The run took too long to complete.")

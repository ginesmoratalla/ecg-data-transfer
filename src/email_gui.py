'''
libraries to import for the file to run

may need to install some libraries that aren't present
in native Python
'''
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

import smtplib
import os

from PyQt5.QtWidgets import *
from PyQt5 import uic

'''
MyGui class
    - subclass of QDialog to import smtp.ui file
    - smtp.ui contains xml components for a simple email ui
      with button and text listeners

    - send_email() function executed when the 'send' button is pressed
      will create an email message with the information typed to the text fields
      + a report PDF with the information on the email body and initialize

      an smtp session to send the email to the desired address
''' 
class MyGui(QDialog):

    def __init__(self):

        super(MyGui, self).__init__()
        uic.loadUi("smtp.ui", self)
        
        self.show()
        self.pushButton.clicked.connect(self.send_email)

    def send_email(self):

        # mail address for SMTP
        sender_email = "youremailaddress@outlook.com"  
        sender_password = "yourpassword"

        # Message destination, subject, and body (button and text listeners) in the GUI
        message_to = self.lineEdit.text()
        message_subject = self.lineEdit_2.text()
        message_body = self.textEdit.toPlainText()

        # Create a PDF report from the content of the email body
        # Using SimpleDocTemplate to respect new lines and spaces (formatting)
        medical_report_pdf = "Medical_Report.pdf"
        doc = SimpleDocTemplate(medical_report_pdf)
        styles = getSampleStyleSheet()
        story = [Paragraph(message_body, styles['BodyText'])]
        doc.build(story)

        # Setup mime - block that creates fields for the email smtp connection
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = message_to
        message['Subject'] = message_subject
        message.attach(MIMEText(message_body, 'plain'))

        # Attach PDF in the message body from the e-mail
        with open(medical_report_pdf, "rb") as attachment:

            # Create a new MIME object to attatch the pdf to the email body
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Add base64 encoding to the pdf (smtp can only handle text data) 
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename= {medical_report_pdf}",)

        # Attatch the encoded PDF into the email body
        message.attach(part)

        # Code piece to create SMTP session using smtplib
        try:

            # Define mail type (otulook) and port
            session = smtplib.SMTP('smtp-mail.outlook.com', 587)
            session.starttls()

            # Log in with the email adress and the password defined above
            session.login(sender_email, sender_password)
            text = message.as_string()

            # Send mail through the smtp session, with the address specified and the body + PDF from message
            session.sendmail(sender_email, message_to, text)

            # End smtp session
            session.quit()
            print('Mail Sent')

        # Exception for failed e-mail connection
        except Exception as e:
            print(f"Failed to send email: {e}")


        # Clear the text fields after sending the email
        self.textEdit.clear()
        self.lineEdit.clear()
        self.lineEdit_2.clear()
        os.remove(medical_report_pdf)


# Execute app window UI
app = QApplication([])
window = MyGui()

# Main execution - block to avoid direct undesired execution of file from other files
if __name__ == "__main__":
    app.exec_()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import qrcode
import boto3
import os
from io import BytesIO
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Root endpoint to avoid 404 error
@app.get("/")
def read_root():
    return {"message": "Welcome to the QR Code Generator API!"}

# Allowing CORS for local testing
origins = [
    "http://54.157.0.91:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS S3 Configuration
try:
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
        region_name=os.getenv("AWS_REGION")  # Optional: add your bucket region if required
    )
    bucket_name = os.getenv("BUCKET_NAME", "bar-code1")  # Default to 'bar-code1'
except Exception as e:
    raise RuntimeError(f"Failed to configure S3: {str(e)}")

@app.post("/generate-qr/")
async def generate_qr(url: str):
    # Sanitize the URL for use as a file name
    sanitized_url = re.sub(r'[^\w\-_.]', '_', url.split('//')[-1])
    file_name = f"qr_codes/{sanitized_url}.png"

    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Save QR Code to a BytesIO object
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    try:
        # Upload to S3
        s3.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=img_byte_arr,
            ContentType='image/png',
            ACL='public-read'
        )

        # Generate the public S3 URL
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
        return {"qr_code_url": s3_url}

    except Exception as e:
        # Log the error and raise an HTTPException
        print(f"Error uploading QR code to S3: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload QR code to S3.")

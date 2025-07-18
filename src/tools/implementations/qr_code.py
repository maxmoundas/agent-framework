# src/tools/implementations/qr_code.py
import qrcode
import io
import base64
from PIL import Image
from ..base import BaseTool
from ..registry import ToolRegistry


@ToolRegistry.register()
class QRCodeTool(BaseTool):
    description = (
        "Generate QR codes for URLs, text, contact information, or WiFi credentials"
    )
    parameters = {
        "content": {
            "type": "string",
            "description": "The content to encode in the QR code (URL, text, contact info, etc.)",
            "required": True,
        },
        "qr_type": {
            "type": "string",
            "description": "Type of QR code content (url, text, contact, wifi). Defaults to 'text'",
            "required": False,
        },
        "size": {
            "type": "integer",
            "description": "Size of the QR code in pixels (default: 200, range: 100-500)",
            "required": False,
        },
        "format": {
            "type": "string",
            "description": "Output format (text, base64, or description). Defaults to 'description'",
            "required": False,
        },
        "name": {
            "type": "string",
            "description": "Name for contact QR codes (required when qr_type is 'contact')",
            "required": False,
        },
        "phone": {
            "type": "string",
            "description": "Phone number for contact QR codes (required when qr_type is 'contact')",
            "required": False,
        },
        "email": {
            "type": "string",
            "description": "Email for contact QR codes (optional when qr_type is 'contact')",
            "required": False,
        },
        "ssid": {
            "type": "string",
            "description": "WiFi network name (required when qr_type is 'wifi')",
            "required": False,
        },
        "password": {
            "type": "string",
            "description": "WiFi password (required when qr_type is 'wifi')",
            "required": False,
        },
        "encryption": {
            "type": "string",
            "description": "WiFi encryption type (WPA, WEP, nopass). Defaults to 'WPA'",
            "required": False,
        },
    }

    def _create_contact_qr_content(self, name, phone, email=None):
        """Create vCard format for contact QR codes"""
        vcard = f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\nTEL:{phone}"
        if email:
            vcard += f"\nEMAIL:{email}"
        vcard += "\nEND:VCARD"
        return vcard

    def _create_wifi_qr_content(self, ssid, password, encryption="WPA"):
        """Create WiFi QR code content"""
        return f"WIFI:T:{encryption};S:{ssid};P:{password};;"

    def _generate_qr_code(self, content, size=200):
        """Generate QR code and return as base64 string"""
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Add data to QR code
        qr.add_data(content)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Resize if needed
        if size != 200:
            img = img.resize((size, size), Image.Resampling.LANCZOS)

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return img_str

    async def execute(
        self,
        content,
        qr_type="text",
        size=200,
        format="description",
        name=None,
        phone=None,
        email=None,
        ssid=None,
        password=None,
        encryption="WPA",
    ):
        """Generate a QR code based on the provided parameters"""
        try:
            # Validate size - convert to int if it's a string
            try:
                size = int(size) if size is not None else 200
            except (ValueError, TypeError):
                size = 200

            # Validate size range
            if size < 100 or size > 500:
                size = 200

            # Determine content based on QR type
            if qr_type.lower() == "contact":
                if not name or not phone:
                    return "Error: Name and phone are required for contact QR codes"
                qr_content = self._create_contact_qr_content(name, phone, email)
                content_type = "Contact Information"

            elif qr_type.lower() == "wifi":
                if not ssid or not password:
                    return "Error: SSID and password are required for WiFi QR codes"
                qr_content = self._create_wifi_qr_content(ssid, password, encryption)
                content_type = "WiFi Network"

            elif qr_type.lower() == "url":
                # Ensure URL has proper scheme
                if not content.startswith(("http://", "https://")):
                    content = "https://" + content
                qr_content = content
                content_type = "URL"

            else:  # text or default
                qr_content = content
                content_type = "Text"

            # Generate QR code
            qr_base64 = self._generate_qr_code(qr_content, size)

            # Return based on format
            if format.lower() == "base64":
                return f"data:image/png;base64,{qr_base64}"

            elif format.lower() == "text":
                return f"QR Code generated successfully!\nContent: {qr_content}\nSize: {size}x{size} pixels"

            else:  # description format (default)
                return f"""QR Code generated successfully!

Content Type: {content_type}
Content: {qr_content}
Size: {size}x{size} pixels

[QR_IMAGE:data:image/png;base64,{qr_base64}]

The QR code contains {len(qr_content)} characters of data and is displayed above."""

        except Exception as e:
            return f"Error generating QR code: {str(e)}"

    def get_setup_instructions(self):
        """Return setup instructions for the QR Code tool"""
        return """
QR Code Tool Setup Instructions:

1. Install the required dependency:
   pip install qrcode[pil]

2. The tool supports multiple QR code types:
   - Text: Plain text content
   - URL: Web addresses (automatically adds https:// if needed)
   - Contact: Contact information in vCard format
   - WiFi: WiFi network credentials

3. Output formats:
   - description: Detailed information about the generated QR code
   - text: Simple confirmation with content
   - base64: Base64 encoded image data

4. The tool automatically handles content formatting and validation.
"""

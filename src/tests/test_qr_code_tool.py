# src/tests/test_qr_code_tool.py
import asyncio
import base64
import io
from PIL import Image
import qrcode
from src.tools.implementations.qr_code import QRCodeTool


class TestQRCodeTool:
    """Test suite for the QR Code Tool"""

    def __init__(self):
        """Initialize test fixtures"""
        self.qr_tool = QRCodeTool()

    def test_tool_registration(self):
        """Test that the tool is properly registered"""
        from src.tools.registry import ToolRegistry

        assert "QRCodeTool" in ToolRegistry.list_tools()

        # Test tool specs
        specs = ToolRegistry.get_tool_specs()
        assert "QRCodeTool" in specs
        assert "content" in specs["QRCodeTool"]["parameters"]

    def test_text_qr_code(self):
        """Test generating a simple text QR code"""

        async def test():
            result = await self.qr_tool.execute(
                content="Hello, World!", qr_type="text", size=200, format="description"
            )

            assert "QR Code generated successfully!" in result
            assert "Content: Hello, World!" in result
            assert "Size: 200x200 pixels" in result
            assert "Content Type: Text" in result
            assert "[QR_IMAGE:" in result

        asyncio.run(test())

    def test_url_qr_code(self):
        """Test generating a URL QR code"""

        async def test():
            result = await self.qr_tool.execute(
                content="google.com", qr_type="url", format="text"
            )

            assert "QR Code generated successfully!" in result
            assert "https://google.com" in result

        asyncio.run(test())

    def test_contact_qr_code(self):
        """Test generating a contact QR code"""

        async def test():
            result = await self.qr_tool.execute(
                content="",  # Not used for contact type
                qr_type="contact",
                name="John Doe",
                phone="+1234567890",
                email="john@example.com",
                format="description",
            )

            assert "QR Code generated successfully!" in result
            assert "Content Type: Contact Information" in result
            assert "BEGIN:VCARD" in result
            assert "FN:John Doe" in result
            assert "TEL:+1234567890" in result
            assert "EMAIL:john@example.com" in result
            assert "[QR_IMAGE:" in result

        asyncio.run(test())

    def test_wifi_qr_code(self):
        """Test generating a WiFi QR code"""

        async def test():
            result = await self.qr_tool.execute(
                content="",  # Not used for wifi type
                qr_type="wifi",
                ssid="MyWiFi",
                password="mypassword123",
                encryption="WPA",
                format="description",
            )

            assert "QR Code generated successfully!" in result
            assert "Content Type: WiFi Network" in result
            assert "WIFI:T:WPA;S:MyWiFi;P:mypassword123;;" in result
            assert "[QR_IMAGE:" in result

        asyncio.run(test())

    def test_base64_format(self):
        """Test generating QR code in base64 format"""

        async def test():
            result = await self.qr_tool.execute(content="Test QR Code", format="base64")

            assert result.startswith("data:image/png;base64,")

            # Verify it's valid base64
            base64_data = result.replace("data:image/png;base64,", "")
            try:
                decoded = base64.b64decode(base64_data)
                # Should be a valid PNG image
                img = Image.open(io.BytesIO(decoded))
                assert img.format == "PNG"
            except Exception as e:
                assert False, f"Invalid base64 data: {e}"

        asyncio.run(test())

    def test_size_validation(self):
        """Test size parameter validation"""

        async def test():
            # Test minimum size
            result = await self.qr_tool.execute(
                content="Test", size=50  # Below minimum
            )
            assert "Size: 200x200 pixels" in result  # Should default to 200

            # Test maximum size
            result = await self.qr_tool.execute(
                content="Test", size=1000  # Above maximum
            )
            assert "Size: 200x200 pixels" in result  # Should default to 200

            # Test valid size
            result = await self.qr_tool.execute(content="Test", size=300)
            assert "Size: 300x300 pixels" in result

            # Test string size (common LLM output)
            result = await self.qr_tool.execute(content="Test", size="300")
            assert "Size: 300x300 pixels" in result

            # Test invalid string size
            result = await self.qr_tool.execute(content="Test", size="invalid")
            assert "Size: 200x200 pixels" in result  # Should default to 200

        asyncio.run(test())

    def test_contact_validation(self):
        """Test contact QR code parameter validation"""

        async def test():
            # Missing required parameters
            result = await self.qr_tool.execute(
                content="",
                qr_type="contact",
                name="John Doe",
                # Missing phone
            )
            assert "Error: Name and phone are required for contact QR codes" in result

            result = await self.qr_tool.execute(
                content="",
                qr_type="contact",
                phone="+1234567890",
                # Missing name
            )
            assert "Error: Name and phone are required for contact QR codes" in result

        asyncio.run(test())

    def test_wifi_validation(self):
        """Test WiFi QR code parameter validation"""

        async def test():
            # Missing required parameters
            result = await self.qr_tool.execute(
                content="",
                qr_type="wifi",
                ssid="MyWiFi",
                # Missing password
            )
            assert "Error: SSID and password are required for WiFi QR codes" in result

            result = await self.qr_tool.execute(
                content="",
                qr_type="wifi",
                password="mypassword123",
                # Missing SSID
            )
            assert "Error: SSID and password are required for WiFi QR codes" in result

        asyncio.run(test())

    def test_qr_code_generation(self):
        """Test the actual QR code generation functionality"""

        async def test():
            result = await self.qr_tool.execute(content="Test Content", format="base64")

            # Extract base64 data
            base64_data = result.replace("data:image/png;base64,", "")
            decoded = base64.b64decode(base64_data)

            # Verify it's a valid QR code
            img = Image.open(io.BytesIO(decoded))
            # QR code size may vary based on content, just check it's square and reasonable
            assert img.size[0] == img.size[1]  # Should be square
            assert img.size[0] >= 200  # Should be at least 200px

            # Test with custom size
            result = await self.qr_tool.execute(
                content="Test Content", size=300, format="base64"
            )

            base64_data = result.replace("data:image/png;base64,", "")
            decoded = base64.b64decode(base64_data)
            img = Image.open(io.BytesIO(decoded))
            # For custom size, it should be closer to the requested size
            assert img.size[0] == img.size[1]  # Should be square
            assert 250 <= img.size[0] <= 350  # Should be around 300px

        asyncio.run(test())

    def test_vcard_format(self):
        """Test vCard format generation"""
        vcard = self.qr_tool._create_contact_qr_content(
            name="Jane Smith", phone="+1987654321", email="jane@example.com"
        )

        expected_lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            "FN:Jane Smith",
            "TEL:+1987654321",
            "EMAIL:jane@example.com",
            "END:VCARD",
        ]

        for line in expected_lines:
            assert line in vcard

    def test_wifi_format(self):
        """Test WiFi format generation"""
        wifi_content = self.qr_tool._create_wifi_qr_content(
            ssid="TestWiFi", password="testpass123", encryption="WPA"
        )

        assert wifi_content == "WIFI:T:WPA;S:TestWiFi;P:testpass123;;"

        # Test different encryption
        wifi_content = self.qr_tool._create_wifi_qr_content(
            ssid="OpenWiFi", password="", encryption="nopass"
        )

        assert wifi_content == "WIFI:T:nopass;S:OpenWiFi;P:;;"

    def test_setup_instructions(self):
        """Test that setup instructions are available"""
        instructions = self.qr_tool.get_setup_instructions()
        assert "qrcode[pil]" in instructions
        assert "Text:" in instructions
        assert "URL:" in instructions
        assert "Contact:" in instructions
        assert "WiFi:" in instructions


def run_tests():
    """Run all tests"""
    test_instance = TestQRCodeTool()

    # Run all test methods
    test_methods = [
        method for method in dir(test_instance) if method.startswith("test_")
    ]

    print("Running QR Code Tool tests...")
    passed = 0
    failed = 0

    for method_name in test_methods:
        try:
            method = getattr(test_instance, method_name)
            method()
            print(f"✓ {method_name}")
            passed += 1
        except Exception as e:
            print(f"✗ {method_name}: {e}")
            failed += 1

    print(f"\nTest Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

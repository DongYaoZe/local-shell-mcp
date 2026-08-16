<!-- i18n-source-sha256: 1f30fc9935125c84fb0838d17ec894d78aaa6253fe3903356414aac716ba2adc -->
# सुरक्षा

सार्वजनिक डिप्लॉयमेंट के लिए OAuth का उपयोग करें। `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN` और `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET` को मजबूत रखें और गोपनीय बनाए रखें।

डिफ़ॉल्ट रूप से, पथ संबंधी कार्रवाइयाँ workspace तक सीमित रहती हैं और संवेदनशील path fragments ब्लॉक किए जाते हैं। Full-container मोड अंतर्निहित workspace और path प्रतिबंधों को निष्क्रिय कर देता है; इसका उपयोग केवल disposable container या VM में करें।

बनाए गए फ़ाइल डाउनलोड लिंक सार्वजनिक bearer URL होते हैं। वे high-entropy token, TTL, वैकल्पिक download-count limit, वैकल्पिक size limit और revocation पर निर्भर करते हैं।

<!-- i18n-source-sha256: ed71ed496e65545264c76f97a154e8e0758faf58be0ba74c24c82f3b860ff4f2 -->
# समस्या निवारण

सेवा की स्थिति जाँचें:

```bash
curl -i http://127.0.0.1:8765/healthz
```

लॉग जाँचें:

```bash
docker compose logs --tail=100 local-shell-mcp
```

यदि ChatGPT कनेक्ट नहीं कर पा रहा है, तो जाँचें कि `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` सार्वजनिक HTTPS origin से बिल्कुल मेल खाता है और `/mcp`, OAuth metadata तथा `/healthz` tunnel या reverse proxy के माध्यम से पहुँच योग्य हैं।

यदि remote workers दिखाई नहीं देते, तो पुष्टि करें कि remote mode सक्षम है, invite की अवधि समाप्त नहीं हुई है और remote machine control server को outbound HTTPS requests भेज सकती है।

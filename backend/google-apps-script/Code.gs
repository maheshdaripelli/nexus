/**
 * Nexus transactional email gateway.
 *
 * Deploy as a Web app:
 *   Execute as: Me
 *   Who has access: Anyone
 *
 * Set Script Property NEXUS_EMAIL_TOKEN to a long random secret before deploying.
 * The caller must send the same token in the JSON request body.
 */
function doPost(e) {
  try {
    const body = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    const expectedToken = PropertiesService.getScriptProperties().getProperty("NEXUS_EMAIL_TOKEN");

    if (!expectedToken || !body.token || !constantTimeEquals_(String(body.token), expectedToken)) {
      return jsonResponse_({ ok: false, error: "Unauthorized" });
    }

    const to = String(body.to || "").trim();
    const subject = String(body.subject || "").trim();
    const htmlBody = String(body.htmlBody || "");
    const textBody = String(body.textBody || "");
    const senderName = String(body.senderName || "Nexus").trim();

    if (!to || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(to)) {
      return jsonResponse_({ ok: false, error: "A valid recipient email is required." });
    }
    if (!subject || (!htmlBody && !textBody)) {
      return jsonResponse_({ ok: false, error: "Subject and email body are required." });
    }

    const remaining = MailApp.getRemainingDailyQuota();
    if (remaining < 1) {
      return jsonResponse_({ ok: false, error: "Google Apps Script daily email quota is exhausted." });
    }

    MailApp.sendEmail({
      to: to,
      subject: subject,
      body: textBody || "Please view this email in an HTML-compatible email client.",
      htmlBody: htmlBody || undefined,
      name: senderName || "Nexus"
    });

    return jsonResponse_({ ok: true, remainingDailyQuota: remaining - 1 });
  } catch (error) {
    console.error("Nexus email gateway error: " + error.message);
    return jsonResponse_({ ok: false, error: "Email gateway failed to send the message." });
  }
}

function doGet() {
  return jsonResponse_({ ok: true, service: "Nexus Google Apps Script email gateway" });
}

function constantTimeEquals_(a, b) {
  if (a.length !== b.length) return false;
  let mismatch = 0;
  for (let i = 0; i < a.length; i++) mismatch |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return mismatch === 0;
}

function jsonResponse_(value) {
  return ContentService
    .createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}

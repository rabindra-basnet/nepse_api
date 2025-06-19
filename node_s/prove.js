import fetch from 'node-fetch';
import https from 'https';

const agent = new https.Agent({
  rejectUnauthorized: false,
});

async function getAuthToken() {
  const response = await fetch("https://www.nepalstock.com/api/authenticate/prove", {
    method: "GET",
    headers: {
      "accept": "application/json, text/plain, */*",
      "accept-language": "en-US,en;q=0.9",
      "cache-control": "no-cache",
      "pragma": "no-cache",
      "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
      "referer": "https://www.nepalstock.com/company/detail/559",
    },
    agent,
    timeout: 5000,
  });

  const data = await response.json();
  return data.accessToken;
}

async function fetchProtectedData(authToken) {
  const response = await fetch("https://www.nepalstock.com/api/nots/security?nonDelisted=true", {
    method: "GET",
    headers: {
      "accept": "application/json, text/plain, */*",
      "accept-language": "en-US,en;q=0.9",
      "cache-control": "no-cache",
      "pragma": "no-cache",
      "authorization": `Salter ${authToken}`, // 👈 Authorization token here
      "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
      "referer": "https://www.nepalstock.com/company/detail/559",
    },
    agent,
    timeout: 5000,
  });

  const data = await response.json();
  console.log("✅ Protected Data:", data);
}

async function main() {
  try {
    const token = await getAuthToken();
    console.log("🔐 Received Token:", token);
    await fetchProtectedData(token);
  } catch (err) {
    console.error("❌ Error:", err.message);
  }
}

main();

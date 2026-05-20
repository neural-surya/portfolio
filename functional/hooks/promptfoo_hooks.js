async function postJson(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${url} returned ${response.status}: ${text}`);
  }
}

function parseFlagsRequired(value) {
  if (!value) {
    return {};
  }

  if (typeof value === 'object') {
    return value;
  }

  if (typeof value !== 'string') {
    return {};
  }

  const trimmed = value.trim();
  if (!trimmed || trimmed === '{}') {
    return {};
  }

  try {
    return JSON.parse(trimmed);
  } catch (error) {
    throw new Error(`Invalid flags_required metadata: ${trimmed}`);
  }
}

export async function resetFlagsBeforeEach(hookName, context) {
  if (hookName === 'afterAll') {
    await postJson('http://localhost:8080/api/flags/reset', {});
    return null;
  }

  if (hookName !== 'beforeEach') {
    return null;
  }

  const test = context.test;
  const metadata = test.metadata || {};
  const baseUrl = metadata.base_url || 'http://localhost:8080';
  const flagsRequired = parseFlagsRequired(metadata.flags_required);

  await postJson(`${baseUrl}/api/flags/reset`, {});

  if (Object.keys(flagsRequired).length > 0) {
    await postJson(`${baseUrl}/api/flags`, { flags: flagsRequired });
  }

  return { test };
}

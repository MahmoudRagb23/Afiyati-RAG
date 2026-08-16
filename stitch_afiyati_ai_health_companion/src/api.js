export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

export async function api(path, options = {}) {
  const token = localStorage.getItem("afiyati_token");
  const isForm = options.body instanceof FormData;
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(isForm ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    let detail = "تعذر إكمال الطلب";
    try {
      const data = await response.json();
      detail = Array.isArray(data.detail)
        ? data.detail.map((item) => item.msg).join("، ")
        : data.detail || detail;
    } catch {
      // Keep the safe, user-facing fallback.
    }
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) return null;
  return response.json();
}


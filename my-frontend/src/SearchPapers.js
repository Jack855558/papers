import React, { useState } from "react";

export default function SearchPapers() {
    const [prompt, setPrompt] = useState("");
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleChange = (e) => {
        setPrompt(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!prompt.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const resp = await fetch("https://my-fastapi-app.onrender.com/query/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ prompt: "example", top_k: 5 })
            });


            if (!resp.ok) {
                throw new Error(`API error: ${resp.status}`);
            }

            const data = await resp.json();
            setResults(data.results || []);
        } catch (err) {
            console.error(err);
            setError("Something went wrong. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: 600, margin: "0 auto", padding: 20 }}>
            <h2>Search Papers</h2>
            <form onSubmit={handleSubmit}>
                <textarea
                    value={prompt}
                    onChange={handleChange}
                    placeholder="Enter your query…"
                    rows={3}
                    style={{ width: "100%", padding: 8, fontSize: 16 }}
                />
                <button
                    type="submit"
                    style={{
                        marginTop: 8,
                        padding: "8px 16px",
                        fontSize: 16,
                        cursor: "pointer",
                    }}
                    disabled={loading}
                >
                    {loading ? "Searching…" : "Search"}
                </button>
            </form>

            {error && (
                <div style={{ color: "red", marginTop: 12 }}>
                    {error}
                </div>
            )}

            {results.length > 0 && (
                <div style={{ marginTop: 24 }}>
                    <h3>Results:</h3>
                    <ul style={{ listStyle: "none", paddingLeft: 0 }}>
                        {results.map((r, idx) => (
                            <li
                                key={idx}
                                style={{
                                    marginBottom: 16,
                                    padding: 12,
                                    border: "1px solid #ddd",
                                    borderRadius: 6,
                                }}
                            >
                                <a
                                    href={r.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{ fontSize: 18, fontWeight: "bold", color: "#0070f3" }}
                                >
                                    {r.title}
                                </a>
                                <p style={{ margin: "4px 0", fontSize: 14, color: "#555" }}>
                                    {r.abstract}
                                </p>
                                <div style={{ fontSize: 12, color: "#888" }}>
                                    Score: {r.score.toFixed(4)}
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

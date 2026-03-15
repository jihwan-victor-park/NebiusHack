export default function FeedbackPanel({ feedback }) {
  if (!feedback) return null;

  return (
    <div className="mt-6 border p-4 rounded bg-yellow-50">
      <h2 className="font-semibold mb-2">LLM Feedback</h2>
      <p>{feedback}</p>
    </div>
  );
}

import { useCallback, useEffect, useState } from "react";

const API = import.meta.env.VITE_API_BASE || window.SMARTTIME_API_BASE || "http://127.0.0.1:8000/api";
const token = () => localStorage.getItem("smartTimeToken");
async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, { ...options, headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), Authorization: `Token ${token()}`, ...options.headers } });
  const data = response.status === 204 ? {} : await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || data.detail || "Request failed.");
  return data;
}

function LeaveManagement() {

  const [leaves, setLeaves] = useState([]);
  const [error, setError] = useState("");
  const loadLeaves = useCallback(async () => {
    try { setLeaves(await api("/leave-requests/")); setError(""); }
    catch (failure) { setError(failure.message); }
  }, []);
  useEffect(() => {
    loadLeaves();
    const timer = window.setInterval(loadLeaves, 30000);
    return () => window.clearInterval(timer);
  }, [loadLeaves]);
  const updateStatus = async (id, newStatus) => {
    try {
      await api(`/leave-requests/${id}/${newStatus === "Approved" ? "approve" : "reject"}/`, { method: "POST", body: JSON.stringify({}) });
      await loadLeaves();
    } catch (failure) { setError(failure.message); }
  };


  return (

    <div>

      <div className="page-header">

        <div>

          <h2>Leave Management</h2>

          <p>
            Review and manage faculty leave requests.
          </p>

        </div>

      </div>

      <div>{error && <p role="alert">{error}</p>}</div>
      <div className="table-container">

        <table>

          <thead>

            <tr>

              <th>Faculty ID</th>

              <th>Applicant</th>

              <th>From</th>

              <th>To</th>

              <th>Reason</th>

              <th>Status</th>

              <th>Actions</th>

            </tr>

          </thead>

          <tbody>

            {leaves.map((leave) => (

              <tr key={leave.id}>

                <td>{leave.faculty_id || leave.faculty_email}</td>

                <td><strong>{leave.faculty_name || leave.faculty_email}</strong></td>

                <td>{leave.from_date}</td>

                <td>{leave.to_date}</td>

                <td>{leave.reason}</td>

                <td>

                  <span
                    className={
                      leave.status === "Approved"
                        ? "badge success"
                        : leave.status === "Rejected"
                        ? "badge rejected"
                        : "badge pending"
                    }
                  >

                    {leave.status}

                  </span>

                </td>

                <td>

                  {leave.status === "Pending" ? (

                    <div className="action-buttons">

                      <button
                        className="approve-button"
                        onClick={() =>
                          updateStatus(leave.id, "Approved")
                        }
                      >

                        Approve

                      </button>

                      <button
                        className="reject-button"
                        onClick={() =>
                          updateStatus(leave.id, "Rejected")
                        }
                      >

                        Reject

                      </button>

                    </div>

                  ) : (

                    <span>Reviewed</span>

                  )}

                </td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    </div>

  );

}

export default LeaveManagement;

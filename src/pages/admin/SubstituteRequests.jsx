import { useCallback, useEffect, useState } from "react";

const API = window.SMARTTIME_API_BASE || "http://127.0.0.1:8000/api";
const token = () => localStorage.getItem("smartTimeToken");
async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, { ...options, headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), Authorization: `Token ${token()}`, ...options.headers } });
  const data = response.status === 204 ? {} : await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || data.detail || "Request failed.");
  return data;
}

function SubstituteRequests() {

  const [requests, setRequests] = useState([]);
  const [error, setError] = useState("");
  const loadRequests = useCallback(async () => {
    try { setRequests(await api("/substitute-requests/")); setError(""); }
    catch (failure) { setError(failure.message); }
  }, []);
  useEffect(() => {
    loadRequests();
    const timer = window.setInterval(loadRequests, 30000);
    return () => window.clearInterval(timer);
  }, [loadRequests]);
  const checkAvailability = async (id) => {
    try { await api(`/substitute-requests/${id}/check_availability/`, { method: "POST", body: JSON.stringify({}) }); await loadRequests(); }
    catch (failure) { setError(failure.message); }
  };
  const approveRequest = async (id) => {
    try { await api(`/substitute-requests/${id}/approve/`, { method: "POST", body: JSON.stringify({}) }); await loadRequests(); }
    catch (failure) { setError(failure.message); }
  };
  const rejectRequest = async (id) => {
    try { await api(`/substitute-requests/${id}/reject/`, { method: "POST", body: JSON.stringify({}) }); await loadRequests(); }
    catch (failure) { setError(failure.message); }
  };


  return (

    <div>

      {/* PAGE HEADER */}

      <div className="page-header">

        <div>

          <h2>Substitute Requests</h2>

          <p>
            Check faculty substitute requests and manage availability.
          </p>

        </div>

      </div>


      {/* REQUEST TABLE */}

      <div>{error && <p role="alert">{error}</p>}</div>
      <div className="table-container">

        <table>

          <thead>

            <tr>

              <th>Faculty ID</th>

              <th>Faculty Name</th>

              <th>Date</th>

              <th>Subject</th>

              <th>Time</th>

              <th>Substitute Teacher</th>

              <th>Availability</th>

              <th>Status</th>

              <th>Actions</th>

            </tr>

          </thead>


          <tbody>

            {requests.map((request) => (

              <tr key={request.id}>

                {/* FACULTY ID */}

                <td>
                  <strong>{request.faculty_id || request.faculty_email}</strong>
                </td>


                {/* FACULTY */}

                <td>
                  {request.faculty_name || request.faculty_email}
                </td>


                {/* DATE */}

                <td>
                  {request.class_date}
                </td>


                {/* SUBJECT */}

                <td>
                  {request.subject}
                </td>


                {/* TIME */}

                <td>
                  {`${request.start_time} - ${request.end_time}`}
                </td>


                {/* SUBSTITUTE */}

                <td>

                  <strong>
                    {request.substitute_name || request.substitute_email || "Not assigned"}
                  </strong>

                  <br />

                  <small>
                    {request.substitute_email || ""}
                  </small>

                </td>


                {/* AVAILABILITY */}

                <td>

                  {request.availability === "Unknown" && (

                    <span className="availability-pending">
                      Not Checked
                    </span>

                  )}


                  {request.availability === "Available" && (

                    <span className="availability-available">
                      Available
                    </span>

                  )}


                  {request.availability === "Not Available" && (

                    <span className="availability-unavailable">
                      Not Available
                    </span>

                  )}

                </td>


                {/* STATUS */}

                <td>

                  <span
                    className={
                      request.status === "Approved"
                        ? "badge approved"
                        : request.status === "Rejected"
                        ? "badge rejected"
                        : "badge pending"
                    }
                  >
                    {request.status}
                  </span>

                </td>


                {/* ACTIONS */}

                <td>

                    <div className="action-buttons">
                        <button
                            className="check-button"
                            onClick={() => checkAvailability(request.id)}
                            disabled={request.status !== "Pending"}>
                                Check Availability
                        </button>

                        <button
                            className="approve-button"
                            onClick={() => approveRequest(request.id)}
                            disabled={request.status !== "Pending" ||
                                request.availability !== "Available"}>
                                Approve
                        </button>

                        <button
                            className="reject-button"
                            onClick={() => rejectRequest(request.id)}
                            disabled={request.status !== "Pending"}>
                                Reject
                        </button>

                    </div>

                </td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    </div>

  );
}

export default SubstituteRequests;

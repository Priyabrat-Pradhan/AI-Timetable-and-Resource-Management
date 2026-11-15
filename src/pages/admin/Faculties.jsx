import { useEffect, useState } from "react";

const API = window.SMARTTIME_API_BASE || "http://127.0.0.1:8000/api";
const authHeaders = () => ({ Authorization: `Token ${localStorage.getItem("smartTimeToken") || ""}`, "Content-Type": "application/json" });
const toFacultyRow = (item) => ({
  id: item.faculty_id || String(item.id),
  userId: item.id,
  teacherId: item.teacher_id,
  name: item.name,
  department: item.department || "",
  email: item.email,
  phone: item.phone || "",
  status: item.status || "Active",
});

function Faculties() {
  const [faculties, setFaculties] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loadError, setLoadError] = useState("");

  const loadFaculties = async () => {
    try {
      const response = await fetch(`${API}/faculty-directory/`, { headers: authHeaders() });
      const data = await response.json().catch(() => []);
      if (!response.ok) throw new Error(data.error || data.detail || "Could not load registered faculty.");
      setFaculties(data.map(toFacultyRow));
      setDepartments((previous) => [...new Set([...previous, ...data.map((item) => item.department).filter(Boolean)])]);
      setLoadError("");
    } catch (error) { setLoadError(error.message); }
  };

  useEffect(() => {
    loadFaculties();
    fetch(`${API}/departments/`, { headers: authHeaders() })
      .then(async (response) => {
        const data = await response.json().catch(() => []);
        if (!response.ok) throw new Error("Could not load departments.");
        setDepartments((previous) => [...new Set([...previous, ...data.map((item) => item.name).filter(Boolean)])]);
      })
      .catch((error) => console.warn(error.message));
    const timer = window.setInterval(loadFaculties, 30000);
    return () => window.clearInterval(timer);
  }, []);

  const [department, setDepartment] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editingFaculty, setEditingFaculty] = useState(null);
  const [formError, setFormError] = useState("");

  const emptyForm = {
    id: "",
    name: "",
    department: "",
    email: "",
    phone: ""
  };

  const [formData, setFormData] = useState(emptyForm);

  // Filter by selected department and search text
  const filteredFaculties = faculties.filter((faculty) => {
    const departmentMatch = !department || faculty.department === department;
    const search = searchTerm.toLowerCase().trim();

    const searchMatch =
      faculty.id.toLowerCase().includes(search) ||
      faculty.name.toLowerCase().includes(search) ||
      faculty.email.toLowerCase().includes(search) ||
      faculty.phone.includes(search);

    return departmentMatch && searchMatch;
  });

  // Open Add Faculty modal
  const handleAddFaculty = () => {
    window.alert("Faculty accounts must register through the Register page. Registered faculty will appear here automatically.");
  };

  // Open Edit Faculty modal
  const handleEditFaculty = (faculty) => {
    setEditingFaculty(faculty);
    setFormData({
      id: faculty.id,
      name: faculty.name,
      department: faculty.department,
      email: faculty.email,
      phone: faculty.phone
    });
    setFormError("");
    setShowModal(true);
  };

  // Handle form inputs
  const handleInputChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value
    }));

    setFormError("");
  };

  // Add or update faculty
  const handleSubmit = async (event) => {
    event.preventDefault();

    const id = formData.id.trim();
    const name = formData.name.trim();
    const email = formData.email.trim();
    const phone = formData.phone.trim();
    const selectedDepartment = formData.department;

    if (!id || !name || !email || !phone) {
      setFormError("Please fill in all fields.");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setFormError("Please enter a valid email address.");
      return;
    }

    if (!/^[0-9]{10}$/.test(phone)) {
      setFormError("Phone number must contain exactly 10 digits.");
      return;
    }

    const duplicateId = faculties.some(
      (faculty) =>
        faculty.id.toLowerCase() === id.toLowerCase() &&
        (!editingFaculty || faculty.id !== editingFaculty.id)
    );

    if (duplicateId) {
      setFormError("Faculty ID already exists.");
      return;
    }

    const duplicateEmail = faculties.some(
      (faculty) =>
        faculty.email.toLowerCase() === email.toLowerCase() &&
        (!editingFaculty || faculty.id !== editingFaculty.id)
    );

    if (duplicateEmail) {
      setFormError("This email address is already registered.");
      return;
    }

    if (!editingFaculty) {
      setFormError("Register the faculty account first, then edit its saved details here.");
      return;
    }

    try {
      const changes = { name, phone };
      if (selectedDepartment) changes.department = selectedDepartment;
      const response = await fetch(`${API}/faculty-directory/${editingFaculty.userId}/`, {
        method: "PATCH", headers: authHeaders(),
        body: JSON.stringify(changes),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || data.detail || "Could not save faculty details.");
      setFaculties((previous) => previous.map((faculty) => faculty.userId === data.id ? toFacultyRow(data) : faculty));
      if (selectedDepartment) setDepartment(selectedDepartment);
    } catch (error) {
      setFormError(error.message);
      return;
    }

    setShowModal(false);
    setEditingFaculty(null);
    setFormData(emptyForm);
    setFormError("");
  };

  // Delete faculty
  const handleDeleteFaculty = (id) => {
    const faculty = faculties.find((item) => item.id === id);

    if (!faculty) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete ${faculty.name}?`
    );

    if (!confirmed) return;

    window.alert("Faculty accounts are retained in the database. Use the status control to mark a faculty member inactive.");
  };

  // Toggle Active / Inactive status
  const handleStatusChange = async (id) => {
    const faculty = faculties.find((item) => item.id === id);
    if (!faculty) return;
    const status = faculty.status === "Active" ? "Inactive" : "Active";
    try {
      const response = await fetch(`${API}/faculty-directory/${faculty.userId}/`, {
        method: "PATCH", headers: authHeaders(), body: JSON.stringify({ status }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || data.detail || "Could not update faculty status.");
      setFaculties((previous) => previous.map((row) => row.userId === data.id ? toFacultyRow(data) : row));
      setLoadError("");
    } catch (error) { setLoadError(error.message); }
  };

  // Close modal
  const closeModal = () => {
    setShowModal(false);
    setEditingFaculty(null);
    setFormError("");
  };

  // Clear search and department
  const handleClearFilters = () => {
    setDepartment("");
    setSearchTerm("");
  };

  return (
    <div className="faculties-page">

      {/* PAGE HEADER */}
      <PageHeader
        title="Faculties"
        description="Manage faculty information department-wise."
      />

      {loadError && <p role="alert">{loadError}</p>}

      {/* TOOLBAR */}
      <div className="toolbar faculty-toolbar">

        {/* DEPARTMENT DROPDOWN */}
        <select
          className="faculty-filter-select"
          value={department}
          onChange={(event) => {
            setDepartment(event.target.value);
            setSearchTerm("");
          }}
        >
          <option value="">Select Department</option>

          {departments.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        {/* SEARCH */}
        <div className="faculty-search student-search">
          <input
            type="text"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Search by ID, name, email or phone..."
          />

          {searchTerm && (
            <button
              type="button"
              className="clear-search-button"
              onClick={() => setSearchTerm("")}
            >
              Clear
            </button>
          )}
        </div>

        {/* CLEAR FILTERS */}
        <button
          type="button"
          className="faculty-clear-button"
          onClick={handleClearFilters}
        >
          Clear Filters
        </button>

        {/* ADD FACULTY */}
        <button
          type="button"
          className="primary-button"
          onClick={handleAddFaculty}
        >
          Add Faculty
        </button>

      </div>

      {/* RESULT INFORMATION */}
      <div className="faculty-result-info">
        {!department ? (
          <span>Showing all registered faculty.</span>
        ) : (
          <span>
            Department: <strong>{department}</strong>
            {" | "}
            Showing <strong>{filteredFaculties.length}</strong> of{" "}
            <strong>
              {faculties.filter((f) => f.department === department).length}
            </strong>{" "}
            faculties
          </span>
        )}
      </div>

      {/* FACULTY TABLE - SHOW AFTER DEPARTMENT SELECTION */}
      {faculties.length > 0 && (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Faculty ID</th>
                <th>Faculty Name</th>
                <th>Email Address</th>
                <th>Phone Number</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {filteredFaculties.length > 0 ? (
                filteredFaculties.map((faculty) => (
                  <tr key={faculty.id}>
                    <td>
                      <strong>{faculty.id}</strong>
                    </td>

                    <td>
                      <strong>{faculty.name}</strong>
                    </td>

                    <td>{faculty.email}</td>

                    <td>{faculty.phone}</td>

                    <td>
                      <button
                        type="button"
                        className={
                          faculty.status === "Active"
                            ? "status-button active-status"
                            : "status-button inactive-status"
                        }
                        onClick={() => handleStatusChange(faculty.id)}
                      >
                        {faculty.status}
                      </button>
                    </td>

                    <td>
                      <div className="faculty-actions">
                        <button
                          type="button"
                          className="table-action edit-action"
                          onClick={() => handleEditFaculty(faculty)}
                        >
                          Edit
                        </button>

                        <button
                          type="button"
                          className="table-action delete-action"
                          onClick={() => handleDeleteFaculty(faculty.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="no-results">
                    No faculties found in this department.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* ADD / EDIT MODAL */}
      {showModal && (
        <div
          className="faculty-modal-overlay"
          onClick={closeModal}
        >
          <div
            className="faculty-modal"
            onClick={(event) => event.stopPropagation()}
          >

            <div className="faculty-modal-header">
              <div>
                <h3>
                  {editingFaculty ? "Edit Faculty" : "Add Faculty"}
                </h3>

                <p>
                  {editingFaculty
                    ? "Update faculty information."
                    : "Enter the faculty information below."}
                </p>
              </div>

              <button
                type="button"
                className="modal-close-button"
                onClick={closeModal}
              >
                Close
              </button>
            </div>

            <form onSubmit={handleSubmit}>

              <div className="faculty-form-group">
                <label>Faculty ID</label>
                <input
                  type="text"
                  name="id"
                  value={formData.id}
                  onChange={handleInputChange}
                  placeholder="Example: T006"
                  disabled={Boolean(editingFaculty)}
                />
              </div>

              <div className="faculty-form-group">
                <label>Faculty Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="Enter faculty name"
                />
              </div>

              <div className="faculty-form-group">
                <label>Department</label>
                <select
                  name="department"
                  value={formData.department}
                  onChange={handleInputChange}
                >
                  <option value="">Select Department</option>

                  {departments.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </div>

              <div className="faculty-form-group">
                <label>Email Address</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  readOnly
                  placeholder="Enter faculty email"
                />
              </div>

              <div className="faculty-form-group">
                <label>Phone Number</label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  placeholder="Enter 10 digit phone number"
                  maxLength="10"
                />
              </div>

              {formError && (
                <div className="faculty-form-error">
                  {formError}
                </div>
              )}

              <div className="faculty-form-buttons">
                <button
                  type="button"
                  className="modal-close-button"
                  onClick={closeModal}
                >
                  Cancel
                </button>

                <button type="submit" className="primary-button">
                  {editingFaculty ? "Update Faculty" : "Add Faculty"}
                </button>
              </div>

            </form>
          </div>
        </div>
      )}

    </div>
  );
}

function PageHeader({ title, description }) {
  return (
    <div className="page-header">
      <div>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default Faculties;

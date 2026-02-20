import { useState } from "react";
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 15000,
});

const initialValues = {
  name: "",
  email: "",
  phone: "",
};

function Form() {
  const [formData, setFormData] = useState(initialValues);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const isFormComplete = Object.values(formData).every((value) => value.trim() !== "");

  const onChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    if (!isFormComplete) {
      setErrorMessage("Please fill in all fields before scheduling.");
      return;
    }
    setIsSubmitting(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const response = await api.post("/schedule", formData);
      if (response?.data?.status === "call_initiated") {
        setSuccessMessage("Call initiated successfully. Please keep your phone available.");
        setFormData(initialValues);
      } else {
        setErrorMessage("Unexpected response from server.");
      }
    } catch (error) {
      const detail =
        error?.response?.data?.detail ||
        "We could not initiate your scheduling call right now. Please try again.";
      setErrorMessage(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="form" onSubmit={onSubmit}>
      <p className="required-note">Fields marked with * are necessary to schedule interview.</p>

      <label htmlFor="name">
        Full Name <span className="required-mark">*</span>
      </label>
      <input
        id="name"
        name="name"
        type="text"
        value={formData.name}
        onChange={onChange}
        required
        placeholder="Enter your full name"
      />

      <label htmlFor="email">
        Email Address <span className="required-mark">*</span>
      </label>
      <input
        id="email"
        name="email"
        type="email"
        value={formData.email}
        onChange={onChange}
        required
        placeholder="Enter your email address"
      />

      <label htmlFor="phone">
        Phone Number <span className="required-mark">*</span>
      </label>
      <input
        id="phone"
        name="phone"
        type="tel"
        value={formData.phone}
        onChange={onChange}
        required
        placeholder="+1 555 123 4567"
      />

      <button type="submit" disabled={isSubmitting || !isFormComplete}>
        {isSubmitting ? "Scheduling..." : "Schedule Interview"}
      </button>

      {successMessage ? <p className="success">{successMessage}</p> : null}
      {errorMessage ? <p className="error">{errorMessage}</p> : null}
    </form>
  );
}

export default Form;

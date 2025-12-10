document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Build participants markup
        let participantsHTML = "";
        const count = details.participants.length;
        if (count > 0) {
          const items = details.participants
            .map((email) => `<li><span class="participant-email">${email}</span><button class="delete-participant" data-activity="${name}" data-email="${email}" aria-label="Remove participant">×</button></li>`)
            .join("");
          participantsHTML = `
            <div class="participants-section">
              <div class="participants-header">
                <span>Participants</span>
                <span class="participant-badge">${count}</span>
              </div>
              <ul class="participants-list">
                ${items}
              </ul>
            </div>
          `;
        } else {
          participantsHTML = `
            <div class="participants-section">
              <div class="participants-header">
                <span>Participants</span>
                <span class="participant-badge">0</span>
              </div>
              <div class="no-participants">No participants yet — be the first to sign up!</div>
            </div>
          `;
        }

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          ${participantsHTML}
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Attach delete event listeners
      attachDeleteListeners();
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle delete participant button clicks
  function attachDeleteListeners() {
    const deleteButtons = document.querySelectorAll(".delete-participant");
    deleteButtons.forEach((button) => {
      button.addEventListener("click", async (event) => {
        event.preventDefault();
        const activity = button.getAttribute("data-activity");
        const email = button.getAttribute("data-email");

        try {
          const response = await fetch(
            `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
            {
              method: "POST",
            }
          );

          const result = await response.json();

          if (response.ok) {
            // Refresh activities to reflect the change
            fetchActivities();
          } else {
            messageDiv.textContent = result.detail || "Failed to unregister participant";
            messageDiv.className = "error";
            messageDiv.classList.remove("hidden");
            setTimeout(() => {
              messageDiv.classList.add("hidden");
            }, 5000);
          }
        } catch (error) {
          messageDiv.textContent = "Failed to unregister participant. Please try again.";
          messageDiv.className = "error";
          messageDiv.classList.remove("hidden");
          console.error("Error unregistering participant:", error);
        }
      });
    });
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        // Refresh activities to reflect the change
        setTimeout(() => {
          fetchActivities();
        }, 1000);
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});

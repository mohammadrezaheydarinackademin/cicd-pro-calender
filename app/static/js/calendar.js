(function () {
  "use strict";

  var dataElement = document.getElementById("calendar-data");
  if (!dataElement) return;

  var data;
  try {
    data = JSON.parse(dataElement.textContent);
  } catch (error) {
    return;
  }

  var csrfMeta = document.querySelector('meta[name="csrf-token"]');
  var csrfToken = csrfMeta ? csrfMeta.getAttribute("content") : "";
  var grid = document.getElementById("week-grid");
  var modal = document.getElementById("event-modal");
  if (!grid || !modal) return;

  var viewPanel = document.getElementById("event-view");
  var formPanel = document.getElementById("event-form");
  var modalTitle = document.getElementById("modal-title");
  var viewTitle = document.getElementById("view-title");
  var viewWhen = document.getElementById("view-when");
  var viewDescription = document.getElementById("view-description");
  var viewError = document.getElementById("view-error");
  var viewEdit = document.getElementById("view-edit");
  var viewDelete = document.getElementById("view-delete");
  var formDelete = document.getElementById("form-delete");
  var formError = document.getElementById("form-error");
  var titleInput = document.getElementById("title");
  var descriptionInput = document.getElementById("description");
  var startDateInput = document.getElementById("start_date");
  var startTimeInput = document.getElementById("start_time");
  var endDateInput = document.getElementById("end_date");
  var endTimeInput = document.getElementById("end_time");
  var formSave = document.getElementById("form-save");

  var currentEventId = null;
  var lastFocused = null;

  function pad(value) {
    return value < 10 ? "0" + value : String(value);
  }

  function padYear(value) {
    var year = String(value);
    while (year.length < 4) year = "0" + year;
    return year;
  }

  function makeLocalDate(year, monthIndex, day, hours, minutes) {
    var value = new Date(0);
    value.setFullYear(year, monthIndex, day);
    value.setHours(hours || 0, minutes || 0, 0, 0);
    return value;
  }

  function parseDateParts(dateString) {
    var parts = dateString.split("-").map(Number);
    return makeLocalDate(parts[0], parts[1] - 1, parts[2], 0, 0);
  }

  function nextDateString(dateString) {
    var parts = dateString.split("-").map(Number);
    var next = makeLocalDate(parts[0], parts[1] - 1, parts[2] + 1, 0, 0);
    return padYear(next.getFullYear()) + "-" + pad(next.getMonth() + 1) + "-" + pad(next.getDate());
  }

  function dayBounds(dateString) {
    return {
      start: dateString + "T00:00",
      end: nextDateString(dateString) + "T00:00"
    };
  }

  function parseLocal(value) {
    var parts = value.split("T");
    if (parts.length !== 2) return new Date(value);
    var dateParts = parts[0].split("-").map(Number);
    var timeParts = parts[1].split(":").map(Number);
    return makeLocalDate(
      dateParts[0],
      dateParts[1] - 1,
      dateParts[2],
      timeParts[0] || 0,
      timeParts[1] || 0
    );
  }

  function formatDate(dateString) {
    var value = parseDateParts(dateString);
    return new Intl.DateTimeFormat("en-GB", {
      weekday: "short",
      day: "numeric",
      month: "short",
      year: "numeric"
    }).format(value);
  }

  function formatWhen(event) {
    if (event.isMultiDay) {
      return (
        formatDate(event.startDate) + ", " + event.startTime +
        " \u2013 " + formatDate(event.endDate) + ", " + event.endTime
      );
    }
    return formatDate(event.startDate) + ", " + event.startTime + " \u2013 " + event.endTime;
  }

  function timeLabel(event, dayDate) {
    if (!event.isMultiDay) return event.startTime + " \u2013 " + event.endTime;
    if (dayDate === event.startDate) return event.startTime + " \u2192";
    if (dayDate === event.endDate) return "\u2192 " + event.endTime;
    return "Ongoing";
  }

  function findEvent(id) {
    if (id === null || id === undefined) return null;
    for (var index = 0; index < data.events.length; index += 1) {
      if (String(data.events[index].id) === String(id)) return data.events[index];
    }
    return null;
  }

  function renderEvents() {
    var containers = grid.querySelectorAll(".day-events");

    containers.forEach(function (container) {
      container.innerHTML = "";
    });

    data.events.forEach(function (event) {
      data.days.forEach(function (day) {
        var bounds = dayBounds(day.date);
        if (event.start < bounds.end && event.end > bounds.start) {
          var container = grid.querySelector('.day-events[data-date="' + day.date + '"]');
          if (!container) return;

          var chip = document.createElement("button");
          chip.type = "button";
          chip.className = "event-chip";
          if (event.isPast) chip.className += " is-past";
          if (event.isMultiDay) chip.className += " is-multiday";
          chip.dataset.id = String(event.id);
          chip.dataset.start = event.start;

          var time = document.createElement("span");
          time.className = "event-time";
          time.textContent = timeLabel(event, day.date);

          var title = document.createElement("span");
          title.className = "event-title";
          title.textContent = event.title;

          chip.appendChild(time);
          chip.appendChild(title);
          container.appendChild(chip);
        }
      });
    });

    containers.forEach(function (container) {
      var chips = Array.prototype.slice.call(container.querySelectorAll(".event-chip"));
      chips.sort(function (first, second) {
        return first.dataset.start.localeCompare(second.dataset.start);
      });
      chips.forEach(function (chip) {
        container.appendChild(chip);
      });
      if (chips.length === 0) {
        var empty = document.createElement("span");
        empty.className = "day-empty";
        empty.textContent = "No events";
        container.appendChild(empty);
      }
    });
  }

  function setFormError(message) {
    if (message) {
      formError.textContent = message;
      formError.hidden = false;
    } else {
      formError.textContent = "";
      formError.hidden = true;
    }
  }

  function setViewError(message) {
    if (message) {
      viewError.textContent = message;
      viewError.hidden = false;
    } else {
      viewError.textContent = "";
      viewError.hidden = true;
    }
  }

  function openModal() {
    lastFocused = document.activeElement;
    modal.hidden = false;
    document.body.classList.add("modal-open");
  }

  function closeModal() {
    modal.hidden = true;
    document.body.classList.remove("modal-open");
    currentEventId = null;
    setFormError("");
    setViewError("");
    if (lastFocused && typeof lastFocused.focus === "function") {
      lastFocused.focus();
    }
  }

  function fillForm(event) {
    titleInput.value = event ? event.title : "";
    descriptionInput.value = event ? event.description : "";
    startDateInput.value = event ? event.startDate : "";
    startTimeInput.value = event ? event.startTime : "09:00";
    endDateInput.value = event ? event.endDate : "";
    endTimeInput.value = event ? event.endTime : "10:00";
  }

  function showForm() {
    viewPanel.hidden = true;
    formPanel.hidden = false;
    modalTitle.textContent = currentEventId ? "Edit event" : "New event";
    formDelete.hidden = currentEventId === null;
    setFormError("");
    setViewError("");
  }

  function openCreate(dateString) {
    currentEventId = null;
    fillForm(null);
    startDateInput.value = dateString;
    endDateInput.value = dateString;
    showForm();
    openModal();
    titleInput.focus();
  }

  function openView(event) {
    currentEventId = event.id;
    viewTitle.textContent = event.title;
    viewWhen.textContent = formatWhen(event);
    viewDescription.textContent = event.description || "No description.";
    viewPanel.hidden = false;
    formPanel.hidden = true;
    modalTitle.textContent = "Event details";
    formDelete.hidden = true;
    setFormError("");
    setViewError("");
    openModal();
    viewEdit.focus();
  }

  function openEdit() {
    var event = findEvent(currentEventId);
    if (!event) return;
    fillForm(event);
    showForm();
    titleInput.focus();
  }

  function buildPayload() {
    return {
      title: titleInput.value.trim(),
      description: descriptionInput.value.trim(),
      start_date: startDateInput.value,
      start_time: startTimeInput.value,
      end_date: endDateInput.value,
      end_time: endTimeInput.value
    };
  }

  function validatePayload(payload) {
    if (!payload.title) return "Title is required.";
    if (!payload.start_date || !payload.start_time || !payload.end_date || !payload.end_time) {
      return "Start and end date/time are required.";
    }
    var start = parseLocal(payload.start_date + "T" + payload.start_time);
    var end = parseLocal(payload.end_date + "T" + payload.end_time);
    if (isNaN(start.getTime()) || isNaN(end.getTime())) {
      return "Enter valid dates and times.";
    }
    if (end <= start) return "End date and time must be after the start.";
    return "";
  }

  function submitForm(event) {
    event.preventDefault();

    var payload = buildPayload();
    var validationError = validatePayload(payload);
    if (validationError) {
      setFormError(validationError);
      return;
    }

    setFormError("");
    formSave.disabled = true;

    var isEdit = currentEventId !== null;
    var url = isEdit ? "/api/events/" + currentEventId : "/api/events";
    var method = isEdit ? "PUT" : "POST";

    fetch(url, {
      method: method,
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken
      },
      body: JSON.stringify(payload)
    })
      .then(function (response) {
        return response.json().catch(function () {
          return {};
        }).then(function (body) {
          if (!response.ok) {
            throw new Error(body.error || "Could not save the event.");
          }
          return body;
        });
      })
      .then(function () {
        window.location.reload();
      })
      .catch(function (error) {
        setFormError(error.message || "Could not save the event.");
        formSave.disabled = false;
      });
  }

  function deleteCurrentEvent() {
    if (currentEventId === null) return;

    var event = findEvent(currentEventId);
    var label = event ? '"' + event.title + '"' : "this event";
    if (!window.confirm("Delete " + label + "? This cannot be undone.")) return;

    viewDelete.disabled = true;
    formDelete.disabled = true;

    fetch("/api/events/" + currentEventId, {
      method: "DELETE",
      headers: {
        "X-CSRF-Token": csrfToken
      }
    })
      .then(function (response) {
        return response.json().catch(function () {
          return {};
        }).then(function (body) {
          if (!response.ok) {
            throw new Error(body.error || "Could not delete the event.");
          }
          return body;
        });
      })
      .then(function () {
        window.location.reload();
      })
      .catch(function (error) {
        setFormError(error.message || "Could not delete the event.");
        setViewError(error.message || "Could not delete the event.");
        viewDelete.disabled = false;
        formDelete.disabled = false;
      });
  }

  grid.addEventListener("click", function (event) {
    var chip = event.target.closest(".event-chip");
    if (chip) {
      var found = findEvent(chip.dataset.id);
      if (found) openView(found);
      return;
    }

    var day = event.target.closest(".day-column");
    if (day) {
      openCreate(day.dataset.date);
    }
  });

  modal.addEventListener("click", function (event) {
    if (event.target === modal) {
      closeModal();
      return;
    }
    if (event.target.closest("[data-close-modal]")) {
      closeModal();
    }
  });

  formPanel.addEventListener("submit", submitForm);
  viewEdit.addEventListener("click", openEdit);
  viewDelete.addEventListener("click", deleteCurrentEvent);
  formDelete.addEventListener("click", deleteCurrentEvent);

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !modal.hidden) {
      closeModal();
    }
  });

  renderEvents();
})();

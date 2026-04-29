import { reactive, readonly } from "vue";

const state = reactive({
  id: null,
  username: "",
  avatar: "",
  email: "",
  phone: "",
  gender: "unknown",
  birth_date: "",
  bio: "",
  date_joined: "",
  last_login: "",
  title: "",
  team: "",
  office: "",
  skills: "",
  delivery_tag: "",
  notify_email: true,
  notify_sms: false,
  remember_device: true,
});

export function useCurrentUser() {
  function loadFromStorage() {
    try {
      const raw = localStorage.getItem("auth_user");
      if (!raw) {
        state.id = null;
        state.username = "";
        state.avatar = "";
        return;
      }
      const u = JSON.parse(raw);
      state.id = u.id ?? null;
      state.username = u.username || "";
      state.avatar = u.avatar || "";
      state.email = u.email || "";
      state.phone = u.phone || "";
      state.gender = u.gender || "unknown";
      state.birth_date = u.birth_date || "";
      state.bio = u.bio || "";
      state.date_joined = u.date_joined || "";
      state.last_login = u.last_login || "";
      state.title = u.title || "";
      state.team = u.team || "";
      state.office = u.office || "";
      state.skills = u.skills || "";
      state.delivery_tag = u.delivery_tag || "";
      state.notify_email = u.notify_email !== false;
      state.notify_sms = Boolean(u.notify_sms);
      state.remember_device = u.remember_device !== false;
    } catch {
      state.id = null;
      state.username = "";
      state.avatar = "";
      state.email = "";
      state.phone = "";
      state.gender = "unknown";
      state.birth_date = "";
      state.bio = "";
      state.date_joined = "";
      state.last_login = "";
      state.title = "";
      state.team = "";
      state.office = "";
      state.skills = "";
      state.delivery_tag = "";
      state.notify_email = true;
      state.notify_sms = false;
      state.remember_device = true;
    }
  }

  function setUser(partial) {
    const next = {
      id: state.id,
      username: state.username,
      avatar: state.avatar,
      email: state.email,
      phone: state.phone,
      gender: state.gender,
      birth_date: state.birth_date,
      bio: state.bio,
      date_joined: state.date_joined,
      last_login: state.last_login,
      title: state.title,
      team: state.team,
      office: state.office,
      skills: state.skills,
      delivery_tag: state.delivery_tag,
      notify_email: state.notify_email,
      notify_sms: state.notify_sms,
      remember_device: state.remember_device,
      ...partial,
    };
    state.id = next.id ?? null;
    state.username = next.username || "";
    state.avatar = next.avatar || "";
    state.email = next.email || "";
    state.phone = next.phone || "";
    state.gender = next.gender || "unknown";
    state.birth_date = next.birth_date || "";
    state.bio = next.bio || "";
    state.date_joined = next.date_joined || "";
    state.last_login = next.last_login || "";
    state.title = next.title || "";
    state.team = next.team || "";
    state.office = next.office || "";
    state.skills = next.skills || "";
    state.delivery_tag = next.delivery_tag || "";
    state.notify_email = next.notify_email !== false;
    state.notify_sms = Boolean(next.notify_sms);
    state.remember_device = next.remember_device !== false;
    localStorage.setItem("auth_user", JSON.stringify(next));
  }

  if (typeof window !== "undefined" && !window.__currentUserLoaded) {
    window.__currentUserLoaded = true;
    loadFromStorage();
    window.addEventListener("storage", (e) => {
      if (e.key === "auth_user") {
        loadFromStorage();
      }
    });
  }

  return {
    user: readonly(state),
    setUser,
    reloadUser: loadFromStorage,
  };
}

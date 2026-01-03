<template>
  <div class="min-h-[calc(100vh-64px)] flex items-center justify-center bg-gradient-to-br from-primary/5 to-secondary/5 p-4">
    <div class="w-full max-w-md card p-6">
      <h1 class="text-xl font-bold mb-4">登录</h1>
      <form class="space-y-3" @submit.prevent="onSubmit">
        <input v-model="username" type="text" placeholder="用户名" class="w-full border rounded px-3 py-2" />
        <input v-model="password" type="password" placeholder="密码" class="w-full border rounded px-3 py-2" />
        <button class="w-full bg-primary text-white py-2 rounded disabled:opacity-50" :disabled="loading">
          {{ loading ? "登录中..." : "登录" }}
        </button>
      </form>
      <p class="text-sm text-info mt-4">没有账户？<router-link to="/register" class="text-primary">去注册</router-link></p>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import http from "@/api/http";
import { apiGetUser } from "@/api/auth";

const router = useRouter();
const username = ref("");
const password = ref("");
const loading = ref(false);

async function onSubmit() {
  if (!username.value || !password.value) {
    alert("请输入用户名和密码");
    return;
  }

  loading.value = true;
  try {
    const formData = new URLSearchParams();
    formData.append("username", username.value);
    formData.append("password", password.value);

    const { data } = await http.post("/api/v1/auth/login", formData);

    if (!data?.access_token) {
      throw new Error("登录失败：未返回 access_token");
    }

    // 保存 JWT Access Token（后端返回 access_token）
    localStorage.setItem("token", data.access_token);

    // 从 JWT 解析 user_id（sub）
    let userId: number | null = null;
    try {
      const payloadPart = data.access_token.split(".")[1];
      const base64 = payloadPart.replace(/-/g, "+").replace(/_/g, "/");
      const json = decodeURIComponent(
        atob(base64)
          .split("")
          .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
          .join("")
      );
      const payload = JSON.parse(json);
      if (payload?.sub != null) {
        const n = Number(payload.sub);
        userId = Number.isFinite(n) ? n : null;
      }
    } catch {
      userId = null;
    }

    // 拉取并存储用户信息（用于 is_admin/个人中心等）
    let userInfo: any = null;
    try {
      // 优先尝试通用的“当前用户”接口（若后端存在）
      const meResp = await http.get("/api/v1/auth/me");
      userInfo = meResp.data;
    } catch {
      // 回退：若能拿到 userId，则尝试通过 users/{id} 获取（管理员可用；普通用户可能 403）
      if (userId != null) {
        try {
          userInfo = await apiGetUser(userId);
        } catch {
          userInfo = null;
        }
      }
    }

    // 严格模式：必须从后端拿到当前用户信息，才能完成登录
    if (!userInfo) {
      localStorage.removeItem("token");
      localStorage.removeItem("session_user");
      localStorage.removeItem("session_is_admin");
      throw new Error("登录失败：无法获取当前用户信息");
    }

    if (userInfo.is_admin === undefined || userInfo.is_admin === null) {
      throw new Error("登录失败：用户信息中缺少 is_admin 字段");
    }

    const adminNum = Number(userInfo.is_admin);

    if (adminNum !== 0 && adminNum !== 1) {
      throw new Error(`登录失败：非法的 is_admin 值（${userInfo.is_admin}）`);
    }

    userInfo.is_admin = adminNum;
    const adminFlag = adminNum;
    localStorage.setItem("session_user", JSON.stringify(userInfo));
    localStorage.setItem("session_is_admin", String(adminFlag));

    // 登录后跳转：管理员到 /cockpit，普通用户到 /user/overview
    if (adminFlag === 1) {
      router.push("/cockpit");
    } else {
      router.push("/user/overview");
    }
  } catch (e: any) {
    // 严格模式：任何失败都不保留本地会话信息
    localStorage.removeItem("token");
    localStorage.removeItem("session_user");
    localStorage.removeItem("session_is_admin");

    const msg = e?.response?.data?.detail || e?.message || "登录失败";
    alert(msg);
  } finally {
    loading.value = false;
  }
}
</script>

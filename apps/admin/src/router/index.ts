import { createRouter, createWebHashHistory } from "vue-router";

import { registerUnauthorizedHandler } from "../api/http";
import { ensureAdminSession } from "../auth/guard";
import { clearAdminSession, hasAdminToken } from "../auth/session";
import AdminLayout from "../layouts/AdminLayout.vue";
import CategoryManagementView from "../views/categories/CategoryManagementView.vue";
import LoginView from "../views/LoginView.vue";
import OrderManagementView from "../views/orders/OrderManagementView.vue";
import ProductManagementView from "../views/products/ProductManagementView.vue";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: LoginView,
      meta: {
        title: "管理员登录",
      },
    },
    {
      path: "/",
      component: AdminLayout,
      meta: {
        requiresAuth: true,
      },
      children: [
        {
          path: "",
          redirect: {
            name: "products",
          },
        },
        {
          path: "products",
          name: "products",
          component: ProductManagementView,
          meta: {
            requiresAuth: true,
            title: "商品管理",
          },
        },
        {
          path: "categories",
          name: "categories",
          component: CategoryManagementView,
          meta: {
            requiresAuth: true,
            title: "分类管理",
          },
        },
        {
          path: "orders",
          name: "orders",
          component: OrderManagementView,
          meta: {
            requiresAuth: true,
            title: "订单管理",
          },
        },
      ],
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: {
        name: "products",
      },
    },
  ],
});

router.beforeEach(async (to) => {
  const requiresAuth = Boolean(to.meta.requiresAuth);

  if (requiresAuth) {
    const isValid = await ensureAdminSession();
    if (!isValid) {
      return {
        name: "login",
        query: {
          redirect: to.fullPath,
        },
      };
    }
  }

  if (to.name === "login" && hasAdminToken()) {
    const isValid = await ensureAdminSession();
    if (isValid) {
      const redirectTarget =
        typeof to.query.redirect === "string" ? to.query.redirect : "/products";
      return redirectTarget;
    }
  }

  return true;
});

registerUnauthorizedHandler(() => {
  const currentRoute = router.currentRoute.value;
  clearAdminSession();

  if (currentRoute.name === "login") {
    return;
  }

  void router.push({
    name: "login",
    query: {
      redirect: currentRoute.fullPath,
    },
  });
});

export default router;

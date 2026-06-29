package com.example.housepredict.config;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class AdminAuthInterceptor implements HandlerInterceptor {
    public static final String SESSION_KEY = "ADMIN_LOGGED_IN";

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        Object loggedIn = request.getSession().getAttribute(SESSION_KEY);
        if (Boolean.TRUE.equals(loggedIn)) {
            return true;
        }
        if (request.getRequestURI().startsWith("/api/admin/")) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"code\":401,\"message\":\"请先登录管理员账号\",\"data\":null}");
            return false;
        }
        response.sendRedirect("/admin/login");
        return false;
    }
}

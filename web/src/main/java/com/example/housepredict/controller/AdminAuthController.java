package com.example.housepredict.controller;

import com.example.housepredict.config.AdminAuthInterceptor;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpSession;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
@Tag(name = "后台登录页面路由", description = "管理员登录、退出相关页面路由。")
public class AdminAuthController {
    private final String adminUsername;
    private final String adminPassword;

    public AdminAuthController(
            @Value("${app.admin.username}") String adminUsername,
            @Value("${app.admin.password}") String adminPassword) {
        this.adminUsername = adminUsername;
        this.adminPassword = adminPassword;
    }

    // 管理员登录页：展示后台登录表单。
    @Operation(summary = "管理员登录页", description = "展示后台管理登录表单。")
    @GetMapping("/admin/login")
    public String loginPage() {
        return "houses/admin_login";
    }

    // 管理员登录提交：校验账号密码，成功后把登录状态写入 Session。
    @Operation(summary = "管理员登录提交", description = "校验管理员账号密码，成功后写入 Session 并跳转后台首页。")
    @PostMapping("/admin/login")
    public String login(
            @RequestParam String username,
            @RequestParam String password,
            @Parameter(hidden = true) HttpSession session,
            @Parameter(hidden = true) Model model) {
        if (adminUsername.equals(username) && adminPassword.equals(password)) {
            session.setAttribute(AdminAuthInterceptor.SESSION_KEY, true);
            session.setAttribute("ADMIN_USERNAME", username);
            return "redirect:/admin/";
        }
        model.addAttribute("error", "账号或密码错误");
        return "houses/admin_login";
    }

    // 管理员退出登录：清空 Session 后回到登录页。
    @Operation(summary = "管理员退出登录", description = "清空登录 Session 并跳转回后台登录页。")
    @GetMapping("/admin/logout")
    public String logout(@Parameter(hidden = true) HttpSession session) {
        session.invalidate();
        return "redirect:/admin/login";
    }
}

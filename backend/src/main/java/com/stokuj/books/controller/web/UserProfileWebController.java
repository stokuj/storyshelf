package com.stokuj.books.controller.web;

import com.stokuj.books.model.entity.User;
import com.stokuj.books.service.UserProfileService;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class UserProfileWebController {

    private final UserProfileService userProfileService;

    public UserProfileWebController(UserProfileService userProfileService) {
        this.userProfileService = userProfileService;
    }

    private boolean hasAuthenticatedUser(Authentication authentication) {
        return authentication != null
                && authentication.isAuthenticated()
                && !(authentication instanceof AnonymousAuthenticationToken);
    }

    @GetMapping("/profile/{username}")
    public String profile(@PathVariable String username,
                          Authentication authentication,
                          Model model) {
        User user = userProfileService.findByUsername(username);
        boolean isOwner = hasAuthenticatedUser(authentication)
                && authentication.getName().equalsIgnoreCase(user.getEmail());

        if (!user.isProfilePublic() && !isOwner) {
            model.addAttribute("status", 403);
            model.addAttribute("error", "Forbidden");
            model.addAttribute("message", "Ten profil jest prywatny.");
            return "error";
        }

        model.addAttribute("profile", userProfileService.toPublicResponse(user));
        model.addAttribute("isOwner", isOwner);
        return "profile";
    }
}

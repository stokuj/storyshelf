package com.stokuj.books.controller.web;

import com.stokuj.books.dto.user.UserProfileUpdateRequest;
import com.stokuj.books.dto.user.UserSettingsResponse;
import com.stokuj.books.service.UserProfileService;
import jakarta.validation.Valid;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
public class UserSettingsController {

    private final UserProfileService userProfileService;

    public UserSettingsController(UserProfileService userProfileService) {
        this.userProfileService = userProfileService;
    }

    @GetMapping("/settings")
    public String settings(Model model, Authentication authentication) {
        UserSettingsResponse settings = userProfileService.toSettingsResponse(
                userProfileService.findByEmail(authentication.getName())
        );
        if (!model.containsAttribute("profileForm")) {
            model.addAttribute("profileForm", new UserProfileUpdateRequest(
                    settings.username(),
                    settings.bio(),
                    settings.avatarUrl()
            ));
        }
        model.addAttribute("settings", settings);
        return "settings";
    }

    @PostMapping("/settings")
    public String updateSettings(@Valid @ModelAttribute("profileForm") UserProfileUpdateRequest request,
                                 org.springframework.validation.BindingResult bindingResult,
                                 Authentication authentication,
                                 RedirectAttributes redirectAttributes,
                                 Model model) {
        if (bindingResult.hasErrors()) {
            UserSettingsResponse settings = userProfileService.toSettingsResponse(
                    userProfileService.findByEmail(authentication.getName())
            );
            model.addAttribute("settings", settings);
            return "settings";
        }

        userProfileService.updateProfile(
                userProfileService.findByEmail(authentication.getName()),
                request
        );
        redirectAttributes.addFlashAttribute("settingsMsg", "Zapisano zmiany profilu.");
        return "redirect:/settings";
    }

    @PostMapping("/settings/visibility")
    public String updateVisibility(@RequestParam("profilePublic") boolean profilePublic,
                                   Authentication authentication,
                                   RedirectAttributes redirectAttributes) {
        userProfileService.updateVisibility(
                userProfileService.findByEmail(authentication.getName()),
                profilePublic
        );
        redirectAttributes.addFlashAttribute("settingsMsg", "Zmieniono widoczność profilu.");
        return "redirect:/settings";
    }
}

package com.stokuj.books.security;

import com.stokuj.books.model.entity.User;
import com.stokuj.books.repository.UserRepository;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.authority.mapping.GrantedAuthoritiesMapper;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.Collection;
import java.util.List;

@Service
public class UserDetailsServiceImpl implements UserDetailsService {

    private final UserRepository userRepository;
    private final GrantedAuthoritiesMapper authoritiesMapper;

    public UserDetailsServiceImpl(UserRepository userRepository,
                                  GrantedAuthoritiesMapper authoritiesMapper) {
        this.userRepository = userRepository;
        this.authoritiesMapper = authoritiesMapper;
    }

    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new UsernameNotFoundException("User not found: " + email));

        Collection<? extends GrantedAuthority> authorities = authoritiesMapper.mapAuthorities(
                List.of(new SimpleGrantedAuthority(user.getRole().asAuthority()))
        );

        return new org.springframework.security.core.userdetails.User(
                user.getEmail(),
                user.getPassword() != null ? user.getPassword() : "",
                user.isEnabled(), true, true, true,
                authorities
        );
    }
}

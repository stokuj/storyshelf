package com.stokuj.books.dto.request;

import com.stokuj.books.model.enums.ReadingStatus;

public class UserBookRequest {

    private ReadingStatus status = ReadingStatus.WANT_TO_READ;

    public ReadingStatus getStatus() {
        return status;
    }

    public void setStatus(ReadingStatus status) {
        this.status = status;
    }
}

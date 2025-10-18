package middlewares

import "errors"

var (
	errInvalidUUID      = errors.New("invalid uuid")
	errNoUUID           = errors.New("no uuid")
	errInvalidJWTToken  = errors.New("invalid JWT Token")
	errUnregisteredUser = errors.New("user is unregistered")
	ErrInvalidToken     = errors.New("invalid token")
	ErrMissingToken     = errors.New("missing token")
)

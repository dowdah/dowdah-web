export const API_VERSION = 'v1';
export const BASE_API_URL = `/api/${API_VERSION}`;
export const ROLE_NAMES = ['User', 'Administrator'];
export const SITE_NAME = 'Dowdah'
export const TURNSTILE_SITE_KEY = '0x4AAAAAABBDvaxOXhwMWkni'
export const TURNSTILE_VERIFY_URL = 'https://turnstile-verify.dowdah.com/'
export const USERNAME_REGEX = /^(?=.{3,20}$)(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$/
export const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).{8,}$/
export const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/

variable "subscription_id" {
  type = string
}

variable "budget_amount" {
  description = "Monthly budget threshold"
  type        = number
  default     = 2000
}

variable "budget_start" {
  type    = string
  default = "2025-01-01T00:00:00Z"
}

variable "budget_end" {
  type    = string
  default = "2026-01-01T00:00:00Z"
}

variable "alert_emails" {
  description = "Emails for budget alerts"
  type        = list(string)
}

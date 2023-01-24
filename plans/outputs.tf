output "feed_processor_charles_haleys_arn" {
    value = aws_lambda_function.feed_processor_charles_haleys.arn
}
output "feed_processor_charles_haleys_role" {
  value = aws_iam_role.feed_processor_charles_haleys_role.name
}
output "feed_processor_charles_haleys_role_arn" {
  value = aws_iam_role.feed_processor_charles_haleys_role.arn
}
output "feed_processor_charles_haleys_policy_arn" {
  value = aws_iam_policy.feed_processor_charles_haleys_policy.arn
}

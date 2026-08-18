resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.railguard.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

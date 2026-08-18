resource "aws_instance" "railguard" {
  ami           = "ami-0734cbe7f841a2e9b"
  instance_type = "t3.micro"

  subnet_id = "subnet-08774c18b4ab308b6"

  vpc_security_group_ids = [
    "sg-0827598cf828f83f6"
  ]

  key_name             = "CloudLabKey"
  iam_instance_profile = "CloudLabEC2S3Role"

  tags = {
    Name = "CloudLabWebServer"
  }
}

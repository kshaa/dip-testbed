package diptestbed.domain

case class TestConfig(testName: Option[String])
object TestConfig {
  def empty: TestConfig = TestConfig(None)
  def fromConfig(enabled: Option[Boolean], testName: Option[String]): TestConfig =
    Option
      .when(enabled.getOrElse(false))(TestConfig(testName))
      .getOrElse(TestConfig.empty)
}

package iotfrisbee.domain.controllers

import scala.concurrent.Future
import scala.concurrent.duration.DurationInt
import akka.stream.Materializer
import akka.util.{ByteString, Timeout}
import cats.effect.IO
import cats.effect.testing.scalatest.AsyncIOSpec
import io.circe._
import io.circe.parser._
import org.scalatest.TestSuite
import org.scalatest.freespec.AsyncFreeSpecLike
import org.scalatest.matchers.should.Matchers
import org.scalatestplus.play.components.WithApplicationComponents
import play.api.mvc.{Action, Headers}
import play.api.test.{FakeRequest, Helpers}
import play.api.test.Helpers.CONTENT_TYPE
import play.api.{BuiltInComponents, Configuration}
import iotfrisbee.web.IotFrisbeeModule
import iotfrisbee.web.ioControls.PipelineOps._

trait IotFrisbeeSpec
    extends TestSuite
    with AsyncFreeSpecLike
    with AsyncIOSpec
    with Matchers
    with WithApplicationComponents {
  implicit def defaultAwaitTimeout: Timeout = 60.seconds
  override def components: BuiltInComponents = null
  val testSuiteName: String = this.getClass.getSimpleName.toLowerCase()
  def module(testName: String = "default"): IotFrisbeeModule =
    new IotFrisbeeModule(
      context.copy(initialConfiguration =
        Configuration(
          "iotfrisbee.test.enabled" -> true,
          "iotfrisbee.test.name" -> f"${testSuiteName}-${testName}",
        ).withFallback(context.initialConfiguration),
      ),
    )
}

object IotFrisbeeSpec {
  def sendJSON[I](method: Action[I], payload: Option[Json] = None)(implicit
    materializer: Materializer,
    timeout: Timeout,
  ): IO[String] =
    method
      .apply(FakeRequest().withHeaders(Headers(CONTENT_TYPE -> "application/json")))
      .run(payload.map(p => ByteString(p.toString())).getOrElse(ByteString.empty))
      .asIO
      .map(x => Helpers.contentAsString(Future.successful(x)))

  def exchangeJSON[I, O: Decoder](method: Action[I], payload: Option[Json] = None)(implicit
    materializer: Materializer,
    timeout: Timeout,
  ): IO[Either[Error, O]] =
    sendJSON(method, payload).map(decode[O])
}

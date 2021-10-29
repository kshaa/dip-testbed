package diptestbed.domain.controllers

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
import diptestbed.web.DIPTestbedModule
import diptestbed.web.ioControls.PipelineOps._

trait DIPTestbedSpec
    extends TestSuite
    with AsyncFreeSpecLike
    with AsyncIOSpec
    with Matchers
    with WithApplicationComponents {
  implicit def defaultAwaitTimeout: Timeout = 60.seconds
  override def components: BuiltInComponents = null
  val testSuiteName: String = this.getClass.getSimpleName.toLowerCase()
  def module(testName: String = "default"): DIPTestbedModule =
    new DIPTestbedModule(
      context.copy(initialConfiguration =
        Configuration(
          // Use centralized pubsub
          "diptestbed.clusterized" -> false,
          // Don't create akka cluster w/ tcp sockets
          "akka.actor.provider" -> "local",
          // Disable distributed pubsub which requires cluster
          "akka.extensions" -> List.empty,
          // Test enabling will result in use of H2 in-memory db
          "diptestbed.test.enabled" -> true,
          // Test name will decide H2 db name
          "diptestbed.test.name" -> f"${testSuiteName}-${testName}",
        ).withFallback(context.initialConfiguration),
      ),
    )
}

object DIPTestbedSpec {
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

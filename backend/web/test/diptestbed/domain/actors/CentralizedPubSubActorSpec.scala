package diptestbed.domain.actors

import diptestbed.web.actors.CentralizedPubSubActor._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.should.Matchers

class CentralizedPubSubActorSpec extends AnyFreeSpec with Matchers {
  "CentralizedPubSubActor" - {
    "should be detect subscription changes" in {
      val subs: Map[String, List[String]] = Map.empty

      val withSub = withSubscription(subs, "topic", "actor1")
      withSub.shouldEqual(Some(Map("topic" -> List("actor1"))))

      val withDuplicateSub = withSub.flatMap(withSubscription(_, "topic", "actor1"))
      withDuplicateSub.shouldEqual(None)

      val withAnotherSub = withSub.flatMap(withSubscription(_, "topic", "actor2"))
      withAnotherSub.shouldEqual(Some(Map("topic" -> List("actor1", "actor2"))))

      val withUnsub = withAnotherSub.flatMap(withoutSubscription(_, "topic", "actor1"))
      withUnsub.shouldEqual(Some(Map("topic" -> List("actor2"))))

      val withDuplicateUnsub = withUnsub.flatMap(withoutSubscription(_, "topic", "actor1"))
      withDuplicateUnsub.shouldEqual(None)
    }
  }
}

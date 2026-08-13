<script setup>
import { nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue'
import PageBanner from '../components/PageBanner.vue'
import PrivacyContent from '../components/PrivacyContent.vue'

defineProps({ trialOnly: { type: Boolean, default: false } })

const submitted = ref(false)
const submitting = ref(false)
const formError = ref('')
const modalOpen = ref(false)
const privacyOpen = ref(false)
const modalRef = ref(null)
const qrCodeUrl = `/ewm.jpg?v=${__BUILD_ID__}`
const form = reactive({
  name: '', phone: '', operatingSystem: '', operatingSystemOther: '', dataSize: '',
  deployment: '', deploymentOther: '', dataTypes: [], dataTypesOther: '', loadTime: '',
  concurrencySupport: '', usedAccelerator: '', expectedLoadTime: '', expectedConcurrency: '',
  acceptableDeployment: [], acceptableDeploymentOther: '', departmentPosition: '',
  organizationType: '', industry: '', industryOther: '', systemUses: [], systemUsesOther: '', privacyAccepted: false,
})

const dataTypeOptions = ['BIM 模型数据', '航拍模型数据', '地图数据', '其它']
const deploymentOptions = ['软硬一体本地部署', '云端部署', '其它']
const useOptions = ['项目设计及优化管理', '项目施工管理', '项目运营管理', '其它']

function openTrial() {
  modalOpen.value = true
  nextTick(() => modalRef.value?.focus())
}

function closeTrial() {
  modalOpen.value = false
}

function openPrivacy() {
  privacyOpen.value = true
}

function closePrivacy() {
  privacyOpen.value = false
}

watch(modalOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})

onBeforeUnmount(() => {
  document.body.style.overflow = ''
})

async function submitApplication() {
  if (submitting.value) return

  formError.value = ''
  submitted.value = false
  const required = [form.name, form.phone, form.operatingSystem, form.dataSize, form.deployment,
    form.loadTime, form.concurrencySupport, form.usedAccelerator, form.expectedLoadTime, form.expectedConcurrency]
  if (required.some((value) => !value) || !form.dataTypes.length || !form.acceptableDeployment.length) {
    formError.value = '请填写所有标注为必填的项目。'
    return
  }
  if ((form.operatingSystem === '其它' && !form.operatingSystemOther.trim()) ||
      (form.deployment === '其它' && !form.deploymentOther.trim()) ||
      (form.dataTypes.includes('其它') && !form.dataTypesOther.trim()) ||
      (form.acceptableDeployment.includes('其它') && !form.acceptableDeploymentOther.trim())) {
    formError.value = '选择“其它”时，请填写具体说明。'
    return
  }
  if (!form.privacyAccepted) {
    formError.value = '请阅读并同意隐私政策后再提交。'
    return
  }

  submitting.value = true
  try {
    const response = await fetch('/appointment', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...form }),
    })

    if (!response.ok) {
      let message = ''
      try {
        const result = await response.json()
        message = result.message || result.msg || result.error || ''
      } catch {
        message = await response.text().catch(() => '')
      }
      throw new Error(message || `服务器返回错误（${response.status}）`)
    }

    submitted.value = true
  } catch (error) {
    formError.value = error instanceof TypeError
      ? '提交失败，请检查网络连接后重试。'
      : `提交失败：${error.message}`
  } finally {
    submitting.value = false
    nextTick(() => document.querySelector('.form-status')?.scrollIntoView({ behavior: 'smooth', block: 'center' }))
  }
}
</script>

<template>
  <template v-if="!trialOnly">
    <PageBanner eyebrow="CONTACT US" title="联系我们" description="欢迎围绕先进科学计算、工业仿真与行业解决方案与我们交流合作。" />
    <section class="section contact-intro">
    <div class="container contact-panel">
      <div class="contact-copy"><p class="eyebrow">GET IN TOUCH</p><h2>合肥栖云科技有限公司</h2><p>安徽省合肥市庐阳区林湖路666号合肥金融广场D2幢408室</p><p>联系邮箱：<a href="mailto:qykjlab@163.com">qykjlab@163.com</a></p></div>
      <figure class="wechat-qr"><img :src="qrCodeUrl" alt="栖云科技微信服务号二维码" /><figcaption><strong>微信服务号</strong><span>微信扫码关注我们</span></figcaption></figure>
    </div>
    </section>
  </template>

  <button v-if="trialOnly" class="btn trial-open-btn" type="button" @click="openTrial">申请试用</button>

  <Teleport to="body">
    <div v-if="modalOpen" ref="modalRef" class="trial-modal" role="dialog" aria-modal="true" aria-labelledby="trial-title" tabindex="-1" @keydown.esc="closeTrial" @mousedown.self="closeTrial">
      <div class="trial-dialog">
        <div class="modal-bar">
          <div><span>PRODUCT TRIAL</span><strong>nuVision 产品试用申请</strong></div>
          <button type="button" aria-label="关闭申请表单" @click="closeTrial">×</button>
        </div>
        <div class="trial-scroll">
    <form class="trial-form" novalidate @submit.prevent="submitApplication">
      <div class="form-title"><p class="eyebrow">TRIAL APPLICATION</p><h2 id="trial-title">产品试用申请</h2><p><span class="required">*</span> 为必填项，您的信息仅用于评估试用需求与后续联系。</p></div>

      <fieldset>
        <legend><span>01</span> 基础信息</legend>
        <div class="form-grid two-cols">
          <label class="field"><span>您的称呼 <b>*</b></span><input v-model.trim="form.name" type="text" autocomplete="name" placeholder="请输入您的称呼" required /></label>
          <label class="field"><span>联系电话 <b>*</b></span><input v-model.trim="form.phone" type="tel" autocomplete="tel" placeholder="请输入联系电话" required /></label>
        </div>
      </fieldset>

      <fieldset>
        <legend><span>02</span> 现有系统基础信息</legend>
        <div class="form-grid two-cols">
          <label class="field"><span>系统运行操作系统 <b>*</b></span><select v-model="form.operatingSystem" required><option disabled value="">请选择</option><option>Windows</option><option>macOS</option><option>Linux</option><option>其它</option></select><input v-if="form.operatingSystem === '其它'" v-model.trim="form.operatingSystemOther" class="other-input" placeholder="请说明操作系统" /></label>
          <label class="field"><span>系统数据大小 <b>*</b></span><select v-model="form.dataSize" required><option disabled value="">请选择</option><option>50G 以下</option><option>50–100G</option><option>100–500G</option><option>500G 及以上</option></select></label>
          <label class="field"><span>系统现有部署方式 <b>*</b></span><select v-model="form.deployment" required><option disabled value="">请选择</option><option>本地部署</option><option>私有云本地调用部署</option><option>公有云云端调用部署</option><option>其它</option></select><input v-if="form.deployment === '其它'" v-model.trim="form.deploymentOther" class="other-input" placeholder="请说明部署方式" /></label>
          <label class="field"><span>系统目前加载时间 <b>*</b></span><select v-model="form.loadTime" required><option disabled value="">请选择</option><option>30 秒以内</option><option>30 秒–2 分钟</option><option>2–5 分钟</option><option>5 分钟以上</option></select></label>
        </div>
        <div class="question"><p>系统数据包含哪些类型？（多选）<b>*</b></p><div class="checks"><label v-for="item in dataTypeOptions" :key="item"><input v-model="form.dataTypes" type="checkbox" :value="item" />{{ item }}</label></div><input v-if="form.dataTypes.includes('其它')" v-model.trim="form.dataTypesOther" class="other-input compact" placeholder="请说明其它数据类型" /></div>
        <div class="form-grid two-cols">
          <div class="question"><p>系统是否支持多用户并发？<b>*</b></p><div class="checks"><label><input v-model="form.concurrencySupport" type="radio" value="是" />是</label><label><input v-model="form.concurrencySupport" type="radio" value="否" />否</label></div></div>
          <div class="question"><p>是否试用过其它加速软件？<b>*</b></p><div class="checks"><label><input v-model="form.usedAccelerator" type="radio" value="是" />是</label><label><input v-model="form.usedAccelerator" type="radio" value="否" />否</label></div></div>
        </div>
      </fieldset>

      <fieldset>
        <legend><span>03</span> 加速功能需求</legend>
        <div class="form-grid two-cols">
          <label class="field"><span>期望的系统加载速度 <b>*</b></span><select v-model="form.expectedLoadTime" required><option disabled value="">请选择</option><option>1 秒以内</option><option>1–10 秒</option><option>10–30 秒</option><option>30 秒以上</option></select></label>
          <label class="field"><span>期望的并发数量 <b>*</b></span><select v-model="form.expectedConcurrency" required><option disabled value="">请选择</option><option>2–50</option><option>50–100</option><option>100–200</option><option>200 以上</option></select></label>
        </div>
        <div class="question"><p>可接受的部署方式（多选）<b>*</b></p><div class="checks"><label v-for="item in deploymentOptions" :key="item"><input v-model="form.acceptableDeployment" type="checkbox" :value="item" />{{ item }}</label></div><input v-if="form.acceptableDeployment.includes('其它')" v-model.trim="form.acceptableDeploymentOther" class="other-input compact" placeholder="请说明其它部署方式" /></div>
      </fieldset>

      <fieldset>
        <legend><span>04</span> 辅助筛选信息 <em>选填</em></legend>
        <p class="fieldset-tip">试用资源有限，提供以下信息将有助于我们加快筛选，您将有机会更快进入试用。</p>
        <div class="form-grid two-cols">
          <label class="field"><span>您的部门与职位</span><input v-model.trim="form.departmentPosition" placeholder="请输入部门与职位" /></label>
          <label class="field"><span>单位性质</span><select v-model="form.organizationType"><option value="">请选择</option><option>政府机关、事业单位</option><option>国有企业</option><option>私营企业</option><option>个人/其它</option></select></label>
          <label class="field"><span>系统所属行业</span><select v-model="form.industry"><option value="">请选择</option><option>国土资源管理（城市规划、海洋、林业、地质等）</option><option>交通、工民建</option><option>能源（电网、新能源、油气管道等）</option><option>其它</option></select><input v-if="form.industry === '其它'" v-model.trim="form.industryOther" class="other-input" placeholder="请说明所属行业" /></label>
        </div>
        <div class="question"><p>系统主要用途（多选）</p><div class="checks"><label v-for="item in useOptions" :key="item"><input v-model="form.systemUses" type="checkbox" :value="item" />{{ item }}</label></div><input v-if="form.systemUses.includes('其它')" v-model.trim="form.systemUsesOther" class="other-input compact" placeholder="请说明其它用途" /></div>
      </fieldset>

      <div class="form-submit">
        <label class="privacy-check"><input v-model="form.privacyAccepted" type="checkbox" required />我已阅读并同意 <button class="privacy-link" type="button" @click="openPrivacy">《隐私政策》</button><b>*</b></label>
        <p v-if="formError" class="form-status error" role="alert">{{ formError }}</p>
        <p v-if="submitted" class="form-status success" role="status">申请已提交成功，我们会尽快与您联系。</p>
        <button class="btn submit-btn" type="submit" :disabled="submitting">{{ submitting ? '正在提交…' : '提交申请' }}</button>
      </div>
    </form>
        </div>
      </div>
    </div>
  </Teleport>

  <Teleport to="body">
    <div v-if="privacyOpen" class="privacy-modal" role="dialog" aria-modal="true" aria-labelledby="privacy-title" tabindex="-1" @keydown.esc.stop="closePrivacy" @mousedown.self="closePrivacy">
      <div class="privacy-dialog">
        <div class="modal-bar">
          <div><span>PRIVACY POLICY</span><strong id="privacy-title">隐私政策</strong></div>
          <button type="button" aria-label="关闭隐私政策" @click="closePrivacy">×</button>
        </div>
        <div class="privacy-scroll"><PrivacyContent /></div>
      </div>
    </div>
  </Teleport>
</template>

import React from 'react'

import '@vaadin/react-components/vaadin-select'
import '@vaadin/react-components/vaadin-checkbox'
import '@vaadin/react-components/vaadin-date-picker'
import '@vaadin/react-components/vaadin-time-picker'
import '@vaadin/react-components/vaadin-text-area'
import '@vaadin/react-components/vaadin-number-field'
import '@vaadin/react-components/vaadin-button'
import '@vaadin/react-components/vaadin-horizontal-layout'
import '@vaadin/react-components/vaadin-vertical-layout'
import '@vaadin/react-components/vaadin-form-layout'
import '@vaadin/react-components/vaadin-notification'

import { Button } from '@vaadin/react-components/Button.js'
import { Select, SelectItem } from '@vaadin/react-components/Select.js'
import { Checkbox } from '@vaadin/react-components/Checkbox.js'
import { DatePicker } from '@vaadin/react-components/DatePicker.js'
import { TimePicker } from '@vaadin/react-components/TimePicker.js'
import { TextArea } from '@vaadin/react-components/TextArea.js'
import { NumberField } from '@vaadin/react-components/NumberField.js'
import { Notification } from '@vaadin/react-components/Notification.js'

export const PTOEntryView: React.FC = () => {
  const [typeOfLeave, setTypeOfLeave] = React.useState<string | null>(null)
  const [wholeDay, setWholeDay] = React.useState<boolean>(true)

  const [date, setDate] = React.useState<string | null>(null)

  const [startDate, setStartDate] = React.useState<string | null>(null)
  const [startTime, setStartTime] = React.useState<string | null>(null)
  const [endDate, setEndDate] = React.useState<string | null>(null)
  const [endTime, setEndTime] = React.useState<string | null>(null)

  const [duration, setDuration] = React.useState<number | null>(null)
  const [description, setDescription] = React.useState<string>('')
  const [note, setNote] = React.useState<string>('')

  React.useEffect(() => {
    if (wholeDay) {
      setDuration(date ? 8 : null)
      return
    }
    if (!(startDate && startTime && endDate && endTime)) {
      setDuration(null)
      return
    }
    const s = new Date(`${startDate}T${startTime}`)
    const e = new Date(`${endDate}T${endTime}`)
    if (isNaN(s.getTime()) || isNaN(e.getTime()) || e <= s) {
      setDuration(null)
      return
    }
    const hours = (e.getTime() - s.getTime()) / (1000 * 60 * 60)
    setDuration(Number(hours.toFixed(2)))
  }, [wholeDay, date, startDate, startTime, endDate, endTime])

  const leaveOptions: SelectItem[] = [
    { label: 'Sick Leave', value: 'Sick Leave' },
    { label: 'Casual Leave', value: 'Casual Leave' },
    { label: 'PTO', value: 'PTO' },
    { label: 'Parental Leave', value: 'Parental Leave' },
  ]

  function submit() {
    // Simple front-end validation per your rules
    if (!typeOfLeave) return Notification.show('Type of Leave is required')
    if (wholeDay) {
      if (!date) return Notification.show('Date is required')
    } else {
      if (!startDate || !startTime || !endDate || !endTime) {
        return Notification.show('Start/End date and time are required')
      }
    }
    if (duration === null) return Notification.show('Duration is invalid')

    Notification.show('Submitted (demo only). Duration: ' + duration + ' hours')
  }

  return (
    <div className="container">
      <div className="h2">PTO Entry</div>

      <div className="section">
        <Select
          label="Type of Leave"
          required
          items={leaveOptions}
          value={typeOfLeave ?? ''}
          onValueChanged={(e) => setTypeOfLeave(e.detail.value || null)}
          className="row-full"
        />

        <Checkbox
          label="Whole Day"
          checked={wholeDay}
          onCheckedChanged={(e) => setWholeDay(e.detail.value)}
          className="row-full"
        />

        {/* Whole day: single date */}
        {wholeDay && (
          <DatePicker
            label="Date"
            required
            value={date ?? ''}
            onValueChanged={(e) => setDate(e.detail.value || null)}
            className="row-full"
          />
        )}

        {/* Half day: start/end date+time */}
        {!wholeDay && (
          <>
            <DatePicker
              label="Start Date"
              required
              value={startDate ?? ''}
              onValueChanged={(e) => setStartDate(e.detail.value || null)}
            />
            <TimePicker
              label="Start Time"
              required
              value={startTime ?? ''}
              onValueChanged={(e) => setStartTime(e.detail.value || null)}
              step={900}
            />
            <DatePicker
              label="End Date"
              required
              value={endDate ?? ''}
              onValueChanged={(e) => setEndDate(e.detail.value || null)}
            />
            <TimePicker
              label="End Time"
              required
              value={endTime ?? ''}
              onValueChanged={(e) => setEndTime(e.detail.value || null)}
              step={900}
            />
          </>
        )}

        <NumberField
          label="Duration (hours)"
          value={duration ?? undefined}
          readonly
          className="row-full"
        />

        <TextArea
          label="Description"
          placeholder="Reason / details"
          value={description}
          onValueChanged={(e) => setDescription(e.detail.value)}
          className="row-full"
        />

        <TextArea
          label="Note for Manager (Private)"
          placeholder="Optional note visible only to your manager"
          value={note}
          onValueChanged={(e) => setNote(e.detail.value)}
          className="row-full"
        />

        <div className="row-full" style={{display: 'flex', gap: 8}}>
          <Button theme="primary" onClick={submit}>Create</Button>
          <Button onClick={() => {
            setTypeOfLeave(null); setWholeDay(true); setDate(null);
            setStartDate(null); setStartTime(null); setEndDate(null); setEndTime(null);
            setDuration(null); setDescription(''); setNote('');
          }}>Cancel</Button>
        </div>
      </div>
    </div>
  )
}
